from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from prices.models import (
    Game,
    PriceObservation,
    SourceReceipt,
    Store,
    StoreProduct,
    VerificationDecision,
)


class CanonicalModelTests(TestCase):
    def make_approved_store(self):
        decision = VerificationDecision.objects.create(
            actor_identity="owner",
            subject_type="STORE",
            subject_identity="steam",
            decision=VerificationDecision.Decision.APPROVED,
            reason="Approved limited read-only viability test",
            immutable_input_identity="a" * 64,
        )
        return Store.objects.create(
            code="steam",
            display_name="Steam",
            source_state=Store.SourceState.APPROVED,
            terms_approval_decision=decision,
        )

    def make_approved_mapping(self):
        store = self.make_approved_store()
        game = Game.objects.create(canonical_title="Cyberpunk 2077", slug="cyberpunk-2077")
        mapping = StoreProduct(
            game=game,
            store=store,
            external_product_id="1091500",
            region="KR",
            currency_expectation="KRW",
            edition_key="standard",
            edition_label="Standard Edition",
            tracking_started_at=timezone.now(),
        )
        decision = VerificationDecision.objects.create(
            actor_identity="owner",
            subject_type="STORE_PRODUCT",
            subject_identity=str(mapping.id),
            decision=VerificationDecision.Decision.APPROVED,
            reason="Approved exact game and edition mapping",
            immutable_input_identity="b" * 64,
        )
        mapping.mapping_state = StoreProduct.MappingState.APPROVED
        mapping.mapping_approval_decision = decision
        mapping.save()
        return mapping

    def test_approved_store_requires_matching_human_decision(self):
        with self.assertRaises(ValidationError):
            Store.objects.create(
                code="steam", display_name="Steam", source_state=Store.SourceState.APPROVED
            )

    def test_approved_mapping_is_product_owned_and_unique(self):
        mapping = self.make_approved_mapping()
        self.assertNotEqual(str(mapping.id), mapping.external_product_id)
        with self.assertRaises(ValidationError):
            StoreProduct.objects.create(
                game=mapping.game,
                store=mapping.store,
                external_product_id="1091500",
                edition_key="standard",
                edition_label="Standard Edition",
                tracking_started_at=timezone.now(),
            )

    def test_mvp_mapping_rejects_non_krw_region(self):
        mapping = self.make_approved_mapping()
        mapping.region = "US"
        mapping.currency_expectation = "USD"
        with self.assertRaises(ValidationError):
            mapping.save()

    def test_observation_constraints_reject_invalid_money(self):
        mapping = self.make_approved_mapping()
        from prices.models import IngestionRun

        run = IngestionRun.objects.create(
            store_product=mapping,
            trigger_actor="worker",
            idempotency_key="invalid-money",
            adapter_revision="fixture-v1",
        )
        receipt = SourceReceipt.objects.create(
            run=run,
            request_method="GET",
            normalized_url="https://store.steampowered.com/api/appdetails?appids=1091500&cc=kr&l=koreana",
            fetched_at=timezone.now(),
            http_status=200,
            response_sha256="c" * 64,
            receipt_identity="d" * 64,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            PriceObservation.objects.create(
                store_product=mapping,
                source_receipt=receipt,
                observation_identity="e" * 64,
                currency="KRW",
                current_amount=20_000,
                regular_amount=10_000,
                fetched_at=timezone.now(),
            )

    def test_append_only_evidence_refuses_model_updates_and_deletes(self):
        decision = VerificationDecision.objects.create(
            actor_identity="owner",
            subject_type="STORE",
            subject_identity="steam",
            decision=VerificationDecision.Decision.REJECTED,
            reason="test",
            immutable_input_identity="f" * 64,
        )
        decision.reason = "changed"
        with self.assertRaises(ValidationError):
            decision.save()
        with self.assertRaises(ValidationError):
            decision.delete()


class AdminBoundaryTests(TestCase):
    def test_anonymous_operator_is_redirected_to_login(self):
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_authenticated_staff_can_open_admin(self):
        user = get_user_model().objects.create_user(
            username="operator", password="synthetic-admin-password", is_staff=True
        )
        self.client.force_login(user)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
