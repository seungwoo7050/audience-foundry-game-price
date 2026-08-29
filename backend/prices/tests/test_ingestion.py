from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from threading import Event

from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from prices.adapters.steam import AdapterError, HttpResponse, normalize_steam_response
from prices.models import (
    AuditEvent,
    Game,
    IngestionRun,
    PriceObservation,
    PublishedPriceProjection,
    SourceReceipt,
    Store,
    StoreProduct,
    VerificationDecision,
)
from prices.services import IngestionConflict, IngestionError, IngestionRejected, run_ingestion


FIXTURE = Path(__file__).parent / "fixtures" / "steam_success.json"


def approved_mapping():
    source_decision = VerificationDecision.objects.create(
        actor_identity="owner",
        subject_type="STORE",
        subject_identity="steam",
        decision="APPROVED",
        reason="approved",
        immutable_input_identity="1" * 64,
    )
    store = Store.objects.create(
        code="steam",
        display_name="Steam",
        source_state="APPROVED",
        terms_approval_decision=source_decision,
    )
    game = Game.objects.create(
        canonical_title="Cyberpunk 2077",
        slug="cyberpunk-2077",
        publication_state="PUBLISHED",
    )
    mapping = StoreProduct(
        game=game,
        store=store,
        external_product_id="1091500",
        region="KR",
        currency_expectation="KRW",
        edition_key="standard",
        edition_label="Standard Edition",
        tracking_started_at=timezone.now() - timedelta(days=1),
    )
    mapping_decision = VerificationDecision.objects.create(
        actor_identity="owner",
        subject_type="STORE_PRODUCT",
        subject_identity=str(mapping.id),
        decision="APPROVED",
        reason="approved mapping",
        immutable_input_identity="2" * 64,
    )
    mapping.mapping_state = "APPROVED"
    mapping.mapping_approval_decision = mapping_decision
    mapping.save()
    return mapping


def candidate(mapping, *, fetched_at=None, current=33_000, receipt_suffix="a"):
    body = FIXTURE.read_bytes()
    normalized = normalize_steam_response(
        external_product_id=mapping.external_product_id,
        normalized_url=(
            "https://store.steampowered.com/api/appdetails"
            "?appids=1091500&cc=kr&l=koreana"
        ),
        response=HttpResponse(200, body, fetched_at or timezone.now()),
    )
    return replace(
        normalized,
        current_amount=current,
        regular_amount=66_000,
        receipt_identity=(normalized.receipt_identity[:-1] + receipt_suffix),
        response_sha256=(normalized.response_sha256[:-1] + receipt_suffix),
    )


class IngestionServiceTests(TestCase):
    def setUp(self):
        self.mapping = approved_mapping()

    def ingest(self, key, value=None, **kwargs):
        value = value or candidate(self.mapping)
        return run_ingestion(
            mapping_id=self.mapping.id,
            idempotency_key=key,
            actor_identity="operator",
            fetcher=lambda _mapping: value,
            **kwargs,
        )

    def test_acceptance_commits_observation_projection_and_audit_once(self):
        result = self.ingest("positive")
        projection = PublishedPriceProjection.objects.get(store_product=self.mapping)
        self.assertEqual(result.outcome, "ACCEPTED")
        self.assertEqual(PriceObservation.objects.count(), 1)
        self.assertEqual(SourceReceipt.objects.count(), 1)
        self.assertEqual(projection.current_amount, 33_000)
        self.assertEqual(projection.observed_low_amount, 33_000)
        self.assertEqual(
            AuditEvent.objects.filter(event_kind="PRICE_OBSERVATION_ACCEPTED").count(), 1
        )

    def test_same_idempotency_key_replays_without_external_fetch(self):
        first = self.ingest("same-key")

        def forbidden(_mapping):
            self.fail("replay performed an external fetch")

        replay = run_ingestion(
            mapping_id=self.mapping.id,
            idempotency_key="same-key",
            actor_identity="operator",
            fetcher=forbidden,
        )
        self.assertEqual(first.observation_id, replay.observation_id)
        self.assertEqual(replay.outcome, "DUPLICATE")
        self.assertEqual(PriceObservation.objects.count(), 1)

    def test_same_receipt_or_same_current_state_is_duplicate(self):
        initial = candidate(self.mapping, receipt_suffix="1")
        self.ingest("first", initial)
        duplicate_receipt = self.ingest("receipt-replay", initial)
        same_state = candidate(
            self.mapping, fetched_at=timezone.now() + timedelta(minutes=1), receipt_suffix="2"
        )
        duplicate_state = self.ingest("state-replay", same_state)
        self.assertEqual(duplicate_receipt.outcome, "DUPLICATE")
        self.assertEqual(duplicate_state.outcome, "DUPLICATE")
        self.assertEqual(PriceObservation.objects.count(), 1)
        self.assertEqual(SourceReceipt.objects.count(), 2)

    def test_out_of_order_observation_is_history_but_not_current(self):
        now = timezone.now()
        newest = candidate(self.mapping, fetched_at=now, current=40_000, receipt_suffix="3")
        older = candidate(
            self.mapping,
            fetched_at=now - timedelta(hours=1),
            current=30_000,
            receipt_suffix="4",
        )
        self.ingest("newest", newest)
        self.ingest("older", older)
        projection = PublishedPriceProjection.objects.get(store_product=self.mapping)
        self.assertEqual(PriceObservation.objects.count(), 2)
        self.assertEqual(projection.current_amount, 40_000)
        self.assertEqual(projection.observed_low_amount, 30_000)

    def test_retryable_external_failure_preserves_state_and_retry_completes_once(self):
        def timeout(_mapping):
            raise AdapterError("NETWORK_FAILURE", retryable=True)

        with self.assertRaises(IngestionRejected):
            run_ingestion(
                mapping_id=self.mapping.id,
                idempotency_key="retry",
                actor_identity="operator",
                fetcher=timeout,
            )
        run = IngestionRun.objects.get(idempotency_key="retry")
        self.assertEqual(run.state, "FAILED_RETRYABLE")
        self.assertFalse(PublishedPriceProjection.objects.exists())
        result = self.ingest("retry", candidate(self.mapping, receipt_suffix="5"))
        self.assertEqual(result.outcome, "ACCEPTED")
        self.assertEqual(PriceObservation.objects.count(), 1)

    def test_unexpected_fetch_failure_is_redacted_and_retryable(self):
        fake_secret = "FAKE_SECRET_SHOULD_NOT_ESCAPE"

        def unexpected(_mapping):
            raise RuntimeError(fake_secret)

        with self.assertRaises(IngestionError) as raised:
            run_ingestion(
                mapping_id=self.mapping.id,
                idempotency_key="unexpected-fetch",
                actor_identity="operator",
                fetcher=unexpected,
            )
        self.assertEqual(raised.exception.code, "INTERNAL_FETCH_FAILURE")
        run = IngestionRun.objects.get(idempotency_key="unexpected-fetch")
        self.assertEqual(run.state, "FAILED_RETRYABLE")
        self.assertEqual(run.failure_message, "INTERNAL_FETCH_FAILURE")
        self.assertNotIn(fake_secret, run.failure_message)
        self.assertFalse(PriceObservation.objects.exists())

    def test_injected_partial_write_rolls_back_then_retries(self):
        value = candidate(self.mapping, receipt_suffix="6")
        with self.assertRaises(IngestionError) as raised:
            self.ingest("fault", value, inject_failure_after_observation=True)
        self.assertEqual(raised.exception.code, "INJECTED_TRANSACTION_FAILURE")
        self.assertFalse(PriceObservation.objects.exists())
        self.assertFalse(SourceReceipt.objects.exists())
        self.assertFalse(PublishedPriceProjection.objects.exists())
        self.assertFalse(AuditEvent.objects.filter(outcome="SUCCESS").exists())
        result = self.ingest("fault", value)
        self.assertEqual(result.outcome, "ACCEPTED")
        self.assertEqual(PriceObservation.objects.count(), 1)

    def test_unapproved_mapping_fails_before_fetch_and_audits_denial(self):
        self.mapping.mapping_state = "PAUSED"
        self.mapping.save()
        called = False

        def forbidden(_mapping):
            nonlocal called
            called = True

        with self.assertRaises(IngestionRejected) as raised:
            run_ingestion(
                mapping_id=self.mapping.id,
                idempotency_key="denied",
                actor_identity="operator",
                fetcher=forbidden,
            )
        self.assertEqual(raised.exception.code, "MAPPING_NOT_APPROVED")
        self.assertFalse(called)
        self.assertFalse(IngestionRun.objects.exists())
        self.assertTrue(AuditEvent.objects.filter(failure_code="MAPPING_NOT_APPROVED").exists())

    def test_observation_before_tracking_start_is_rejected_without_canonical_write(self):
        too_early = candidate(
            self.mapping,
            fetched_at=self.mapping.tracking_started_at - timedelta(seconds=1),
            receipt_suffix="9",
        )
        with self.assertRaises(IngestionRejected) as raised:
            self.ingest("before-tracking", too_early)
        self.assertEqual(raised.exception.code, "OBSERVATION_BEFORE_TRACKING_START")
        self.assertFalse(SourceReceipt.objects.exists())
        self.assertFalse(PriceObservation.objects.exists())
        self.assertFalse(PublishedPriceProjection.objects.exists())


class ConcurrentIngestionTests(TransactionTestCase):
    reset_sequences = True

    def test_concurrent_same_key_creates_at_most_one_observation(self):
        mapping = approved_mapping()
        entered = Event()
        release = Event()

        def slow_fetch(_mapping):
            entered.set()
            release.wait(timeout=5)
            return candidate(mapping, receipt_suffix="7")

        def first_request():
            close_old_connections()
            try:
                return run_ingestion(
                    mapping_id=mapping.id,
                    idempotency_key="concurrent",
                    actor_identity="operator-a",
                    fetcher=slow_fetch,
                )
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(first_request)
            self.assertTrue(entered.wait(timeout=5))
            with self.assertRaises(IngestionConflict) as raised:
                run_ingestion(
                    mapping_id=mapping.id,
                    idempotency_key="concurrent",
                    actor_identity="operator-b",
                    fetcher=lambda _mapping: candidate(mapping, receipt_suffix="8"),
                )
            self.assertEqual(raised.exception.code, "RUN_ALREADY_ACTIVE")
            release.set()
            self.assertEqual(future.result(timeout=5).outcome, "ACCEPTED")
        self.assertEqual(IngestionRun.objects.count(), 1)
        self.assertEqual(PriceObservation.objects.count(), 1)
