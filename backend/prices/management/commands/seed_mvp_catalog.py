import hashlib
import uuid
from datetime import UTC, datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from prices.models import Game, Store, StoreProduct, VerificationDecision


GAME_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")
MAPPING_ID = uuid.UUID("22222222-2222-4222-8222-222222222222")
SOURCE_DECISION_ID = uuid.UUID("33333333-3333-4333-8333-333333333333")
MAPPING_DECISION_ID = uuid.UUID("44444444-4444-4444-8444-444444444444")


class Command(BaseCommand):
    help = "Seed the explicitly approved Cyberpunk 2077 MVP mapping in a disposable database"

    def add_arguments(self, parser):
        parser.add_argument("--actor", required=True)
        parser.add_argument("--human-approved", action="store_true", required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        actor = options["actor"]
        approval_hash = hashlib.sha256(
            b"2026-08-29|steam-appdetails|1091500|KR|Standard Edition"
        ).hexdigest()
        source_decision, _ = VerificationDecision.objects.get_or_create(
            id=SOURCE_DECISION_ID,
            defaults={
                "actor_identity": actor,
                "subject_type": "STORE",
                "subject_identity": "steam",
                "decision": VerificationDecision.Decision.APPROVED,
                "reason": "Human-approved one-product read-only Steam viability request",
                "immutable_input_identity": approval_hash,
            },
        )
        store, _ = Store.objects.get_or_create(
            code="steam",
            defaults={
                "display_name": "Steam",
                "source_state": Store.SourceState.APPROVED,
                "terms_approval_decision": source_decision,
            },
        )
        game, _ = Game.objects.get_or_create(
            id=GAME_ID,
            defaults={
                "canonical_title": "Cyberpunk 2077",
                "slug": "cyberpunk-2077",
                "publication_state": Game.PublicationState.PUBLISHED,
            },
        )
        mapping_decision, _ = VerificationDecision.objects.get_or_create(
            id=MAPPING_DECISION_ID,
            defaults={
                "actor_identity": actor,
                "subject_type": "STORE_PRODUCT",
                "subject_identity": str(MAPPING_ID),
                "decision": VerificationDecision.Decision.APPROVED,
                "reason": "Human-approved Cyberpunk 2077 Standard Edition mapping",
                "immutable_input_identity": approval_hash,
            },
        )
        mapping, _ = StoreProduct.objects.get_or_create(
            id=MAPPING_ID,
            defaults={
                "game": game,
                "store": store,
                "external_product_id": "1091500",
                "region": "KR",
                "currency_expectation": "KRW",
                "edition_key": "standard",
                "edition_label": "Standard Edition",
                "mapping_state": StoreProduct.MappingState.APPROVED,
                "tracking_started_at": datetime(2026, 8, 29, tzinfo=UTC),
                "mapping_approval_decision": mapping_decision,
            },
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"game_id={game.id} mapping_id={mapping.id} approval_identity={approval_hash}"
            )
        )
