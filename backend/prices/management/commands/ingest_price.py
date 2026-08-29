import json
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from prices.adapters.steam import HttpResponse, normalize_steam_response
from prices.services import IngestionError, run_ingestion


class Command(BaseCommand):
    help = "Run one approved synchronous price ingestion"

    def add_arguments(self, parser):
        parser.add_argument("mapping_id")
        parser.add_argument("--idempotency-key", required=True)
        parser.add_argument("--actor", required=True)
        parser.add_argument("--fixture", type=Path)
        parser.add_argument("--fetched-at")

    def handle(self, *args, **options):
        fetcher = None
        if options["fixture"]:
            fixture_path = options["fixture"]
            fetched_at = (
                datetime.fromisoformat(options["fetched_at"].replace("Z", "+00:00"))
                if options["fetched_at"]
                else timezone.now()
            )

            def fetcher(mapping):
                normalized_url = (
                    "https://store.steampowered.com/api/appdetails"
                    f"?appids={mapping.external_product_id}&cc=kr&l=koreana"
                )
                return normalize_steam_response(
                    external_product_id=mapping.external_product_id,
                    normalized_url=normalized_url,
                    response=HttpResponse(200, fixture_path.read_bytes(), fetched_at),
                )

        kwargs = {
            "mapping_id": options["mapping_id"],
            "idempotency_key": options["idempotency_key"],
            "actor_identity": options["actor"],
        }
        if fetcher:
            kwargs["fetcher"] = fetcher
        try:
            result = run_ingestion(**kwargs)
        except IngestionError as exc:
            raise CommandError(exc.code) from None
        self.stdout.write(
            json.dumps(
                {
                    "run_id": result.run_id,
                    "outcome": result.outcome,
                    "observation_id": result.observation_id,
                    "receipt_id": result.receipt_id,
                },
                sort_keys=True,
            )
        )
