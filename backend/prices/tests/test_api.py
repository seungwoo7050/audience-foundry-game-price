import json
import uuid
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from django.test import TestCase
from django.urls import reverse

from prices.adapters.steam import HttpResponse, normalize_steam_response
from prices.models import (
    Game,
    IngestionRun,
    PriceObservation,
    PublishedPriceProjection,
    Store,
    StoreProduct,
    VerificationDecision,
)
from prices.services import run_ingestion


HERE = Path(__file__).parent


class GamePriceApiTests(TestCase):
    def setUp(self):
        source_decision = VerificationDecision.objects.create(
            id=uuid.UUID("33333333-3333-4333-8333-333333333333"),
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
        self.game = Game.objects.create(
            id=uuid.UUID("11111111-1111-4111-8111-111111111111"),
            canonical_title="Cyberpunk 2077",
            slug="cyberpunk-2077",
            publication_state="PUBLISHED",
        )
        mapping_id = uuid.UUID("22222222-2222-4222-8222-222222222222")
        mapping_decision = VerificationDecision.objects.create(
            id=uuid.UUID("44444444-4444-4444-8444-444444444444"),
            actor_identity="owner",
            subject_type="STORE_PRODUCT",
            subject_identity=str(mapping_id),
            decision="APPROVED",
            reason="approved",
            immutable_input_identity="2" * 64,
        )
        self.mapping = StoreProduct.objects.create(
            id=mapping_id,
            game=self.game,
            store=store,
            external_product_id="1091500",
            region="KR",
            currency_expectation="KRW",
            edition_key="standard",
            edition_label="Standard Edition",
            mapping_state="APPROVED",
            tracking_started_at=datetime(2026, 8, 1, tzinfo=UTC),
            mapping_approval_decision=mapping_decision,
        )
        body = (HERE / "fixtures" / "steam_success.json").read_bytes()
        candidate = normalize_steam_response(
            external_product_id="1091500",
            normalized_url=(
                "https://store.steampowered.com/api/appdetails"
                "?appids=1091500&cc=kr&l=koreana"
            ),
            response=HttpResponse(200, body, datetime(2026, 8, 29, 2, tzinfo=UTC)),
        )
        candidate = replace(candidate, receipt_identity="a" * 64)
        run_ingestion(
            mapping_id=self.mapping.id,
            idempotency_key="api-contract",
            actor_identity="operator",
            fetcher=lambda _mapping: candidate,
        )

    def test_exact_v1_contract_matches_checked_in_fixture(self):
        response = self.client.get(reverse("game-price-v1", args=[self.game.slug]))
        expected = json.loads((HERE / "contracts" / "game-price-v1.json").read_text())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)
        self.assertEqual(response.headers["Cache-Control"], "public, max-age=60")

    def test_unpublished_or_unknown_game_is_not_exposed(self):
        self.game.publication_state = "SUSPENDED"
        self.game.save()
        suspended = self.client.get(reverse("game-price-v1", args=[self.game.slug]))
        missing = self.client.get(reverse("game-price-v1", args=["unknown-game"]))
        self.assertEqual(suspended.status_code, 404)
        self.assertEqual(missing.status_code, 404)

    def test_public_contract_rejects_mutation_and_excludes_internal_evidence(self):
        before = (
            IngestionRun.objects.count(),
            PriceObservation.objects.count(),
            PublishedPriceProjection.objects.count(),
        )
        response = self.client.post(
            reverse("game-price-v1", args=[self.game.slug]),
            data={"current_amount_minor": 1},
        )
        self.assertEqual(response.status_code, 405)
        self.assertEqual(
            before,
            (
                IngestionRun.objects.count(),
                PriceObservation.objects.count(),
                PublishedPriceProjection.objects.count(),
            ),
        )
        public = self.client.get(reverse("game-price-v1", args=[self.game.slug])).content.decode()
        for forbidden in ["receipt", "audit", "actor", "idempotency", "approval", "FAKE_SECRET"]:
            self.assertNotIn(forbidden.lower(), public.lower())
