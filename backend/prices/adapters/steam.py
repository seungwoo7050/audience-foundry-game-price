from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from django.utils import timezone


ADAPTER_REVISION = "steam-appdetails-v1"
REQUEST_TIMEOUT_SECONDS = 10.0
MAX_RESPONSE_BYTES = 1_000_000
STORE_HOST = "store.steampowered.com"
STORE_PATH = "/api/appdetails"


class AdapterError(Exception):
    def __init__(self, code: str, *, retryable: bool = False):
        self.code = code
        self.retryable = retryable
        super().__init__(code)


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: bytes
    fetched_at: datetime


@dataclass(frozen=True)
class SteamCandidate:
    external_product_id: str
    source_title: str
    currency: str
    current_amount: int
    regular_amount: int | None
    discount_percent: int | None
    source_observed_at: datetime | None
    normalized_url: str
    fetched_at: datetime
    http_status: int
    response_sha256: str
    receipt_identity: str
    adapter_revision: str = ADAPTER_REVISION


def build_normalized_url(external_product_id: str) -> str:
    if not external_product_id.isdigit():
        raise AdapterError("INVALID_EXTERNAL_PRODUCT_ID")
    query = urlencode(
        [("appids", external_product_id), ("cc", "kr"), ("l", "koreana")]
    )
    return f"https://{STORE_HOST}{STORE_PATH}?{query}"


def _is_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require_amount(value: object, code: str) -> int:
    if not _is_integer(value) or value < 0:
        raise AdapterError(code)
    return value


def normalize_steam_response(
    *, external_product_id: str, normalized_url: str, response: HttpResponse
) -> SteamCandidate:
    response_hash = hashlib.sha256(response.body).hexdigest()
    receipt_identity = hashlib.sha256(
        f"GET\n{normalized_url}\n{response_hash}".encode()
    ).hexdigest()
    if response.status != 200:
        retryable = response.status == 429 or response.status >= 500
        raise AdapterError(f"HTTP_STATUS_{response.status}", retryable=retryable)
    try:
        payload = json.loads(response.body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise AdapterError("INVALID_JSON") from None
    if not isinstance(payload, dict) or set(payload) != {external_product_id}:
        raise AdapterError("PRODUCT_ID_MISMATCH")
    product = payload[external_product_id]
    if not isinstance(product, dict) or product.get("success") is not True:
        raise AdapterError("SOURCE_PRODUCT_FAILURE")
    data = product.get("data")
    if not isinstance(data, dict) or str(data.get("steam_appid")) != external_product_id:
        raise AdapterError("PRODUCT_ID_MISMATCH")
    price = data.get("price_overview")
    if not isinstance(price, dict):
        raise AdapterError("MISSING_CURRENT_PRICE")
    currency = price.get("currency")
    if currency != "KRW":
        raise AdapterError("UNSUPPORTED_CURRENCY")
    current_amount = _require_amount(price.get("final"), "INVALID_CURRENT_AMOUNT")
    regular_value = price.get("initial")
    regular_amount = (
        None if regular_value is None else _require_amount(regular_value, "INVALID_REGULAR_AMOUNT")
    )
    if regular_amount is not None and current_amount > regular_amount:
        raise AdapterError("CURRENT_EXCEEDS_REGULAR")
    discount_value = price.get("discount_percent")
    if discount_value is None:
        discount_percent = None
    elif not _is_integer(discount_value) or not 0 <= discount_value <= 100:
        raise AdapterError("INVALID_DISCOUNT")
    else:
        discount_percent = discount_value
    if regular_amount is not None and discount_percent is not None:
        if (current_amount == regular_amount and discount_percent != 0) or (
            current_amount < regular_amount and discount_percent == 0
        ):
            raise AdapterError("INCONSISTENT_DISCOUNT")
    title = data.get("name")
    if not isinstance(title, str) or not title.strip():
        raise AdapterError("MISSING_PRODUCT_TITLE")
    return SteamCandidate(
        external_product_id=external_product_id,
        source_title=title.strip(),
        currency=currency,
        current_amount=current_amount,
        regular_amount=regular_amount,
        discount_percent=discount_percent,
        source_observed_at=None,
        normalized_url=normalized_url,
        fetched_at=response.fetched_at,
        http_status=response.status,
        response_sha256=response_hash,
        receipt_identity=receipt_identity,
    )


def _default_transport(url: str, timeout: float) -> HttpResponse:
    request = Request(url, method="GET", headers={"User-Agent": "GamePrice-KR-MVP/1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            final_url = urlparse(response.geturl())
            if final_url.scheme != "https" or final_url.hostname != STORE_HOST:
                raise AdapterError("UNSAFE_REDIRECT")
            body = response.read(MAX_RESPONSE_BYTES + 1)
            if len(body) > MAX_RESPONSE_BYTES:
                raise AdapterError("RESPONSE_TOO_LARGE")
            return HttpResponse(
                status=response.status,
                body=body,
                fetched_at=timezone.now(),
            )
    except HTTPError as exc:
        retryable = exc.code == 429 or exc.code >= 500
        raise AdapterError(f"HTTP_STATUS_{exc.code}", retryable=retryable) from None
    except (TimeoutError, URLError, OSError):
        raise AdapterError("NETWORK_FAILURE", retryable=True) from None


def fetch_steam_candidate(
    mapping, *, transport: Callable[[str, float], HttpResponse] = _default_transport
) -> SteamCandidate:
    if mapping.region != "KR" or mapping.currency_expectation != "KRW":
        raise AdapterError("UNSUPPORTED_MAPPING_REGION_OR_CURRENCY")
    normalized_url = build_normalized_url(mapping.external_product_id)
    try:
        response = transport(normalized_url, REQUEST_TIMEOUT_SECONDS)
    except AdapterError:
        raise
    except (TimeoutError, URLError, OSError):
        raise AdapterError("NETWORK_FAILURE", retryable=True) from None
    return normalize_steam_response(
        external_product_id=mapping.external_product_id,
        normalized_url=normalized_url,
        response=response,
    )
