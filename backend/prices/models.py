import uuid

from django.core.exceptions import ValidationError
from django.db import models


class SchemaVersionedModel(models.Model):
    schema_version = models.PositiveSmallIntegerField(default=1, editable=False)

    class Meta:
        abstract = True


class AppendOnlyModel(SchemaVersionedModel):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(f"{type(self).__name__} is append-only")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(f"{type(self).__name__} is append-only")


class VerificationDecision(AppendOnlyModel):
    class Decision(models.TextChoices):
        APPROVED = "APPROVED"
        REJECTED = "REJECTED"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor_identity = models.CharField(max_length=150)
    subject_type = models.CharField(max_length=40)
    subject_identity = models.CharField(max_length=150)
    decision = models.CharField(max_length=16, choices=Decision.choices)
    reason = models.TextField()
    immutable_input_identity = models.CharField(max_length=64)
    decided_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["decided_at", "id"]

    def __str__(self):
        return f"{self.subject_type}:{self.subject_identity} {self.decision}"


class Game(SchemaVersionedModel):
    class PublicationState(models.TextChoices):
        DRAFT = "DRAFT"
        PUBLISHED = "PUBLISHED"
        SUSPENDED = "SUSPENDED"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    canonical_title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    publication_state = models.CharField(
        max_length=16, choices=PublicationState.choices, default=PublicationState.DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.canonical_title


class Store(SchemaVersionedModel):
    class SourceState(models.TextChoices):
        DRAFT = "DRAFT"
        APPROVED = "APPROVED"
        REJECTED = "REJECTED"
        PAUSED = "PAUSED"

    code = models.SlugField(max_length=40, primary_key=True)
    display_name = models.CharField(max_length=120)
    source_state = models.CharField(
        max_length=16, choices=SourceState.choices, default=SourceState.DRAFT
    )
    terms_approval_decision = models.ForeignKey(
        VerificationDecision, null=True, blank=True, on_delete=models.PROTECT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.source_state == self.SourceState.APPROVED:
            decision = self.terms_approval_decision
            if not decision or decision.decision != VerificationDecision.Decision.APPROVED:
                raise ValidationError({"terms_approval_decision": "Approved source decision required"})
            if decision.subject_type != "STORE" or decision.subject_identity != self.code:
                raise ValidationError({"terms_approval_decision": "Decision subject does not match store"})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name


class StoreProduct(SchemaVersionedModel):
    class MappingState(models.TextChoices):
        DRAFT = "DRAFT"
        APPROVED = "APPROVED"
        REJECTED = "REJECTED"
        PAUSED = "PAUSED"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game = models.ForeignKey(Game, on_delete=models.PROTECT, related_name="store_products")
    store = models.ForeignKey(Store, on_delete=models.PROTECT, related_name="products")
    external_product_id = models.CharField(max_length=80)
    region = models.CharField(max_length=2, default="KR")
    currency_expectation = models.CharField(max_length=3, default="KRW")
    edition_key = models.SlugField(max_length=80)
    edition_label = models.CharField(max_length=120)
    mapping_state = models.CharField(
        max_length=16, choices=MappingState.choices, default=MappingState.DRAFT
    )
    tracking_started_at = models.DateTimeField()
    mapping_approval_decision = models.ForeignKey(
        VerificationDecision, null=True, blank=True, on_delete=models.PROTECT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["store", "external_product_id", "region", "edition_key"],
                name="unique_store_product_identity",
            ),
            models.CheckConstraint(condition=models.Q(region="KR"), name="mvp_region_is_kr"),
            models.CheckConstraint(
                condition=models.Q(currency_expectation="KRW"), name="mvp_currency_is_krw"
            ),
        ]

    def clean(self):
        if self.region != "KR" or self.currency_expectation != "KRW":
            raise ValidationError("MVP store products must be KR/KRW")
        if self.mapping_state == self.MappingState.APPROVED:
            decision = self.mapping_approval_decision
            if not decision or decision.decision != VerificationDecision.Decision.APPROVED:
                raise ValidationError({"mapping_approval_decision": "Approved mapping decision required"})
            if decision.subject_type != "STORE_PRODUCT" or decision.subject_identity != str(self.id):
                raise ValidationError({"mapping_approval_decision": "Decision subject does not match mapping"})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.store_id}:{self.external_product_id}:{self.edition_key}"


class IngestionRun(SchemaVersionedModel):
    class State(models.TextChoices):
        QUEUED = "QUEUED"
        RUNNING = "RUNNING"
        SUCCEEDED = "SUCCEEDED"
        FAILED_RETRYABLE = "FAILED_RETRYABLE"
        FAILED_FINAL = "FAILED_FINAL"

    class CandidateState(models.TextChoices):
        RECEIVED = "RECEIVED"
        ACCEPTED = "ACCEPTED"
        REJECTED = "REJECTED"
        DUPLICATE = "DUPLICATE"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store_product = models.ForeignKey(StoreProduct, on_delete=models.PROTECT, related_name="runs")
    trigger_actor = models.CharField(max_length=150)
    idempotency_key = models.CharField(max_length=128, unique=True)
    state = models.CharField(max_length=24, choices=State.choices, default=State.QUEUED)
    candidate_state = models.CharField(
        max_length=16, choices=CandidateState.choices, default=CandidateState.RECEIVED
    )
    adapter_revision = models.CharField(max_length=64)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    failure_code = models.CharField(max_length=64, blank=True)
    failure_message = models.CharField(max_length=240, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["store_product"],
                condition=models.Q(state__in=["QUEUED", "RUNNING"]),
                name="one_active_run_per_store_product",
            )
        ]


class SourceReceipt(AppendOnlyModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(IngestionRun, on_delete=models.PROTECT, related_name="receipts")
    request_method = models.CharField(max_length=8)
    normalized_url = models.URLField(max_length=500)
    fetched_at = models.DateTimeField()
    http_status = models.PositiveSmallIntegerField(null=True, blank=True)
    response_sha256 = models.CharField(max_length=64)
    receipt_identity = models.CharField(max_length=64, unique=True)
    source_revision_metadata = models.JSONField(default=dict)
    redaction_status = models.CharField(max_length=24, default="REDACTED")


class PriceObservation(AppendOnlyModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store_product = models.ForeignKey(
        StoreProduct, on_delete=models.PROTECT, related_name="observations"
    )
    source_receipt = models.OneToOneField(
        SourceReceipt, on_delete=models.PROTECT, related_name="accepted_observation"
    )
    observation_identity = models.CharField(max_length=64, unique=True)
    currency = models.CharField(max_length=3)
    current_amount = models.BigIntegerField()
    regular_amount = models.BigIntegerField(null=True, blank=True)
    discount_percent = models.PositiveSmallIntegerField(null=True, blank=True)
    source_observed_at = models.DateTimeField(null=True, blank=True)
    fetched_at = models.DateTimeField()
    accepted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(currency="KRW"), name="observation_currency_krw"),
            models.CheckConstraint(condition=models.Q(current_amount__gte=0), name="current_amount_nonnegative"),
            models.CheckConstraint(
                condition=models.Q(regular_amount__isnull=True)
                | models.Q(regular_amount__gte=models.F("current_amount")),
                name="regular_not_below_current",
            ),
            models.CheckConstraint(
                condition=models.Q(discount_percent__isnull=True)
                | models.Q(discount_percent__range=(0, 100)),
                name="discount_percentage_bounded",
            ),
        ]


class AuditEvent(AppendOnlyModel):
    class Outcome(models.TextChoices):
        SUCCESS = "SUCCESS"
        REJECTED = "REJECTED"
        DUPLICATE = "DUPLICATE"
        FAILED_RETRYABLE = "FAILED_RETRYABLE"
        FAILED_FINAL = "FAILED_FINAL"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor_type = models.CharField(max_length=32)
    actor_identity = models.CharField(max_length=150)
    event_kind = models.CharField(max_length=64)
    subject_identity = models.CharField(max_length=150)
    immutable_input_identity = models.CharField(max_length=128)
    occurred_at = models.DateTimeField(auto_now_add=True)
    outcome = models.CharField(max_length=24, choices=Outcome.choices)
    failure_code = models.CharField(max_length=64, blank=True)
    related_run = models.ForeignKey(
        IngestionRun, null=True, blank=True, on_delete=models.PROTECT, related_name="audit_events"
    )
    redaction_status = models.CharField(max_length=24, default="REDACTED")

    class Meta:
        ordering = ["occurred_at", "id"]


class PublishedPriceProjection(SchemaVersionedModel):
    store_product = models.OneToOneField(
        StoreProduct, primary_key=True, on_delete=models.CASCADE, related_name="published_price"
    )
    latest_observation = models.ForeignKey(
        PriceObservation, on_delete=models.PROTECT, related_name="latest_for_projections"
    )
    observed_low_observation = models.ForeignKey(
        PriceObservation, on_delete=models.PROTECT, related_name="low_for_projections"
    )
    currency = models.CharField(max_length=3)
    current_amount = models.BigIntegerField()
    regular_amount = models.BigIntegerField(null=True, blank=True)
    discount_percent = models.PositiveSmallIntegerField(null=True, blank=True)
    observed_low_amount = models.BigIntegerField()
    tracking_started_at = models.DateTimeField()
    published_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(currency="KRW"), name="projection_currency_krw"),
            models.CheckConstraint(condition=models.Q(current_amount__gte=0), name="projection_current_nonnegative"),
            models.CheckConstraint(
                condition=models.Q(observed_low_amount__gte=0), name="projection_low_nonnegative"
            ),
        ]
