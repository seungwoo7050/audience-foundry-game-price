from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Callable

from django.db import IntegrityError, transaction
from django.utils import timezone

from .adapters.steam import ADAPTER_REVISION, AdapterError, SteamCandidate, fetch_steam_candidate
from .models import (
    AuditEvent,
    IngestionRun,
    PriceObservation,
    PublishedPriceProjection,
    SourceReceipt,
    Store,
    StoreProduct,
)


class IngestionError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class IngestionRejected(IngestionError):
    pass


class IngestionConflict(IngestionError):
    pass


class InjectedTransactionFailure(Exception):
    pass


@dataclass(frozen=True)
class IngestionResult:
    run_id: str
    outcome: str
    observation_id: str | None
    receipt_id: str | None


def _audit(
    *,
    actor_identity: str,
    event_kind: str,
    subject_identity: str,
    immutable_input_identity: str,
    outcome: str,
    run: IngestionRun | None = None,
    failure_code: str = "",
) -> AuditEvent:
    return AuditEvent.objects.create(
        actor_type="INGESTION_WORKER",
        actor_identity=actor_identity,
        event_kind=event_kind,
        subject_identity=subject_identity,
        immutable_input_identity=immutable_input_identity,
        outcome=outcome,
        failure_code=failure_code,
        related_run=run,
        redaction_status="REDACTED",
    )


def _mapping_is_approved(mapping: StoreProduct) -> bool:
    return (
        mapping.mapping_state == StoreProduct.MappingState.APPROVED
        and mapping.store.source_state == Store.SourceState.APPROVED
        and mapping.mapping_approval_decision_id is not None
        and mapping.store.terms_approval_decision_id is not None
    )


def _existing_result(run: IngestionRun) -> IngestionResult:
    receipt = run.receipts.order_by("fetched_at", "id").first()
    observation = None
    if receipt is not None:
        observation = PriceObservation.objects.filter(source_receipt=receipt).first()
    return IngestionResult(
        run_id=str(run.id),
        outcome=IngestionRun.CandidateState.DUPLICATE,
        observation_id=str(observation.id) if observation else None,
        receipt_id=str(receipt.id) if receipt else None,
    )


def _start_run(
    *, mapping_id, idempotency_key: str, actor_identity: str, adapter_revision: str
) -> tuple[StoreProduct, IngestionRun, IngestionResult | None]:
    with transaction.atomic():
        mapping = (
            StoreProduct.objects.select_for_update()
            .select_related("store")
            .get(pk=mapping_id)
        )
        if not _mapping_is_approved(mapping):
            raise IngestionRejected("MAPPING_NOT_APPROVED")
        existing = IngestionRun.objects.select_for_update().filter(
            idempotency_key=idempotency_key
        ).first()
        if existing:
            if existing.store_product_id != mapping.id:
                raise IngestionConflict("IDEMPOTENCY_KEY_SCOPE_MISMATCH")
            if existing.state == IngestionRun.State.SUCCEEDED:
                _audit(
                    actor_identity=actor_identity,
                    event_kind="INGESTION_REPLAY",
                    subject_identity=str(mapping.id),
                    immutable_input_identity=idempotency_key,
                    outcome=AuditEvent.Outcome.DUPLICATE,
                    run=existing,
                )
                return mapping, existing, _existing_result(existing)
            if existing.state in [IngestionRun.State.QUEUED, IngestionRun.State.RUNNING]:
                _audit(
                    actor_identity=actor_identity,
                    event_kind="INGESTION_CONFLICT",
                    subject_identity=str(mapping.id),
                    immutable_input_identity=idempotency_key,
                    outcome=AuditEvent.Outcome.DUPLICATE,
                    run=existing,
                    failure_code="RUN_ALREADY_ACTIVE",
                )
                raise IngestionConflict("RUN_ALREADY_ACTIVE")
            if existing.state == IngestionRun.State.FAILED_FINAL:
                raise IngestionRejected("RUN_FAILED_FINAL")
            existing.state = IngestionRun.State.RUNNING
            existing.started_at = timezone.now()
            existing.ended_at = None
            existing.failure_code = ""
            existing.failure_message = ""
            existing.save(
                update_fields=[
                    "state",
                    "started_at",
                    "ended_at",
                    "failure_code",
                    "failure_message",
                ]
            )
            return mapping, existing, None
        try:
            run = IngestionRun.objects.create(
                store_product=mapping,
                trigger_actor=actor_identity,
                idempotency_key=idempotency_key,
                state=IngestionRun.State.RUNNING,
                adapter_revision=adapter_revision,
                started_at=timezone.now(),
            )
        except IntegrityError as exc:
            raise IngestionConflict("RUN_ALREADY_ACTIVE") from exc
        return mapping, run, None


def _record_failure(
    *, run_id, actor_identity: str, code: str, retryable: bool
) -> None:
    with transaction.atomic():
        run = IngestionRun.objects.select_for_update().get(pk=run_id)
        run.state = (
            IngestionRun.State.FAILED_RETRYABLE
            if retryable
            else IngestionRun.State.FAILED_FINAL
        )
        run.candidate_state = IngestionRun.CandidateState.REJECTED
        run.failure_code = code
        run.failure_message = code
        run.ended_at = timezone.now()
        run.save(
            update_fields=[
                "state",
                "candidate_state",
                "failure_code",
                "failure_message",
                "ended_at",
            ]
        )
        _audit(
            actor_identity=actor_identity,
            event_kind="INGESTION_FAILED",
            subject_identity=str(run.store_product_id),
            immutable_input_identity=run.idempotency_key,
            outcome=(
                AuditEvent.Outcome.FAILED_RETRYABLE
                if retryable
                else AuditEvent.Outcome.FAILED_FINAL
            ),
            run=run,
            failure_code=code,
        )


def _observation_identity(mapping: StoreProduct, candidate: SteamCandidate) -> str:
    normalized = {
        "store_product_id": str(mapping.id),
        "currency": candidate.currency,
        "current_amount": candidate.current_amount,
        "regular_amount": candidate.regular_amount,
        "discount_percent": candidate.discount_percent,
        "source_observed_at": (
            candidate.source_observed_at.isoformat() if candidate.source_observed_at else None
        ),
        "receipt_identity": candidate.receipt_identity,
    }
    return hashlib.sha256(
        json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _ordering_key(observation: PriceObservation) -> tuple:
    return (
        observation.source_observed_at or observation.fetched_at,
        observation.source_receipt.receipt_identity,
    )


def _candidate_ordering_key(candidate: SteamCandidate) -> tuple:
    return (candidate.source_observed_at or candidate.fetched_at, candidate.receipt_identity)


def _same_published_state(
    projection: PublishedPriceProjection | None, candidate: SteamCandidate
) -> bool:
    return bool(
        projection
        and projection.currency == candidate.currency
        and projection.current_amount == candidate.current_amount
        and projection.regular_amount == candidate.regular_amount
        and projection.discount_percent == candidate.discount_percent
    )


def _accept_candidate(
    *,
    run_id,
    candidate: SteamCandidate,
    actor_identity: str,
    inject_failure_after_observation: bool,
) -> IngestionResult:
    with transaction.atomic():
        run = IngestionRun.objects.select_for_update().select_related("store_product__store").get(
            pk=run_id
        )
        mapping = StoreProduct.objects.select_for_update().select_related("store").get(
            pk=run.store_product_id
        )
        if not _mapping_is_approved(mapping):
            raise IngestionRejected("MAPPING_APPROVAL_CHANGED")
        candidate_time = candidate.source_observed_at or candidate.fetched_at
        if candidate_time < mapping.tracking_started_at:
            raise IngestionRejected("OBSERVATION_BEFORE_TRACKING_START")
        existing_receipt = SourceReceipt.objects.filter(
            receipt_identity=candidate.receipt_identity
        ).first()
        if existing_receipt:
            run.state = IngestionRun.State.SUCCEEDED
            run.candidate_state = IngestionRun.CandidateState.DUPLICATE
            run.ended_at = timezone.now()
            run.save(update_fields=["state", "candidate_state", "ended_at"])
            _audit(
                actor_identity=actor_identity,
                event_kind="INGESTION_DUPLICATE_RECEIPT",
                subject_identity=str(mapping.id),
                immutable_input_identity=candidate.receipt_identity,
                outcome=AuditEvent.Outcome.DUPLICATE,
                run=run,
            )
            return IngestionResult(str(run.id), "DUPLICATE", None, str(existing_receipt.id))
        receipt = SourceReceipt.objects.create(
            run=run,
            request_method="GET",
            normalized_url=candidate.normalized_url,
            fetched_at=candidate.fetched_at,
            http_status=candidate.http_status,
            response_sha256=candidate.response_sha256,
            receipt_identity=candidate.receipt_identity,
            source_revision_metadata={"adapter_revision": candidate.adapter_revision},
            redaction_status="REDACTED",
        )
        projection = PublishedPriceProjection.objects.select_for_update().filter(
            store_product=mapping
        ).first()
        if _same_published_state(projection, candidate):
            run.state = IngestionRun.State.SUCCEEDED
            run.candidate_state = IngestionRun.CandidateState.DUPLICATE
            run.ended_at = timezone.now()
            run.save(update_fields=["state", "candidate_state", "ended_at"])
            _audit(
                actor_identity=actor_identity,
                event_kind="INGESTION_DUPLICATE_STATE",
                subject_identity=str(mapping.id),
                immutable_input_identity=candidate.receipt_identity,
                outcome=AuditEvent.Outcome.DUPLICATE,
                run=run,
            )
            return IngestionResult(str(run.id), "DUPLICATE", None, str(receipt.id))
        observation = PriceObservation.objects.create(
            store_product=mapping,
            source_receipt=receipt,
            observation_identity=_observation_identity(mapping, candidate),
            currency=candidate.currency,
            current_amount=candidate.current_amount,
            regular_amount=candidate.regular_amount,
            discount_percent=candidate.discount_percent,
            source_observed_at=candidate.source_observed_at,
            fetched_at=candidate.fetched_at,
        )
        if inject_failure_after_observation:
            raise InjectedTransactionFailure
        if projection is None:
            projection = PublishedPriceProjection.objects.create(
                store_product=mapping,
                latest_observation=observation,
                observed_low_observation=observation,
                currency=observation.currency,
                current_amount=observation.current_amount,
                regular_amount=observation.regular_amount,
                discount_percent=observation.discount_percent,
                observed_low_amount=observation.current_amount,
                tracking_started_at=mapping.tracking_started_at,
            )
        else:
            if _candidate_ordering_key(candidate) > _ordering_key(projection.latest_observation):
                projection.latest_observation = observation
                projection.currency = observation.currency
                projection.current_amount = observation.current_amount
                projection.regular_amount = observation.regular_amount
                projection.discount_percent = observation.discount_percent
            if observation.current_amount < projection.observed_low_amount:
                projection.observed_low_amount = observation.current_amount
                projection.observed_low_observation = observation
            projection.save()
        _audit(
            actor_identity=actor_identity,
            event_kind="PRICE_OBSERVATION_ACCEPTED",
            subject_identity=str(observation.id),
            immutable_input_identity=candidate.receipt_identity,
            outcome=AuditEvent.Outcome.SUCCESS,
            run=run,
        )
        run.state = IngestionRun.State.SUCCEEDED
        run.candidate_state = IngestionRun.CandidateState.ACCEPTED
        run.ended_at = timezone.now()
        run.save(update_fields=["state", "candidate_state", "ended_at"])
        return IngestionResult(
            str(run.id), "ACCEPTED", str(observation.id), str(receipt.id)
        )


def run_ingestion(
    *,
    mapping_id,
    idempotency_key: str,
    actor_identity: str,
    fetcher: Callable[[StoreProduct], SteamCandidate] = fetch_steam_candidate,
    inject_failure_after_observation: bool = False,
) -> IngestionResult:
    if not idempotency_key or len(idempotency_key) > 128:
        raise IngestionRejected("INVALID_IDEMPOTENCY_KEY")
    try:
        mapping, run, replay = _start_run(
            mapping_id=mapping_id,
            idempotency_key=idempotency_key,
            actor_identity=actor_identity,
            adapter_revision=ADAPTER_REVISION,
        )
    except IngestionRejected as exc:
        _audit(
            actor_identity=actor_identity,
            event_kind="INGESTION_DENIED",
            subject_identity=str(mapping_id),
            immutable_input_identity=idempotency_key,
            outcome=AuditEvent.Outcome.REJECTED,
            failure_code=exc.code,
        )
        raise
    if replay:
        return replay
    try:
        candidate = fetcher(mapping)
    except AdapterError as exc:
        _record_failure(
            run_id=run.id,
            actor_identity=actor_identity,
            code=exc.code,
            retryable=exc.retryable,
        )
        raise IngestionRejected(exc.code) from None
    except Exception:
        _record_failure(
            run_id=run.id,
            actor_identity=actor_identity,
            code="INTERNAL_FETCH_FAILURE",
            retryable=True,
        )
        raise IngestionError("INTERNAL_FETCH_FAILURE") from None
    try:
        return _accept_candidate(
            run_id=run.id,
            candidate=candidate,
            actor_identity=actor_identity,
            inject_failure_after_observation=inject_failure_after_observation,
        )
    except InjectedTransactionFailure:
        _record_failure(
            run_id=run.id,
            actor_identity=actor_identity,
            code="INJECTED_TRANSACTION_FAILURE",
            retryable=True,
        )
        raise IngestionError("INJECTED_TRANSACTION_FAILURE") from None
    except IngestionRejected as exc:
        _record_failure(
            run_id=run.id,
            actor_identity=actor_identity,
            code=exc.code,
            retryable=False,
        )
        raise
    except Exception:
        _record_failure(
            run_id=run.id,
            actor_identity=actor_identity,
            code="INTERNAL_PERSISTENCE_FAILURE",
            retryable=True,
        )
        raise IngestionError("INTERNAL_PERSISTENCE_FAILURE") from None
