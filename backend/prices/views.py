from datetime import UTC

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from .models import Game, PublishedPriceProjection, Store, StoreProduct


def _utc_iso(value):
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


@require_GET
def game_price(request, slug):
    projection = get_object_or_404(
        PublishedPriceProjection.objects.select_related(
            "store_product__game", "store_product__store", "latest_observation"
        ),
        store_product__game__slug=slug,
        store_product__game__publication_state=Game.PublicationState.PUBLISHED,
        store_product__mapping_state=StoreProduct.MappingState.APPROVED,
        store_product__store__source_state=Store.SourceState.APPROVED,
    )
    mapping = projection.store_product
    latest = projection.latest_observation
    payload = {
        "schema_version": 1,
        "game": {
            "id": str(mapping.game_id),
            "slug": mapping.game.slug,
            "title": mapping.game.canonical_title,
        },
        "price": {
            "store_product_id": str(mapping.id),
            "source": {"code": mapping.store_id, "name": mapping.store.display_name},
            "edition": {"key": mapping.edition_key, "label": mapping.edition_label},
            "region": mapping.region,
            "currency": projection.currency,
            "current_amount_minor": projection.current_amount,
            "regular_amount_minor": projection.regular_amount,
            "discount_percent": projection.discount_percent,
            "observed_low_amount_minor": projection.observed_low_amount,
            "observed_low_scope": "SINCE_TRACKING_BEGAN",
            "observed_low_label": "추적 시작 이후 관찰된 최저가",
            "tracking_started_at": _utc_iso(projection.tracking_started_at),
            "latest_observed_at": _utc_iso(
                latest.source_observed_at or latest.fetched_at
            ),
        },
    }
    response = JsonResponse(payload, json_dumps_params={"ensure_ascii": False})
    response.headers["Cache-Control"] = "public, max-age=60"
    return response
