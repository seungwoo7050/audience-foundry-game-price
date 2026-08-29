from datetime import datetime, UTC
from pathlib import Path
from types import SimpleNamespace

from django.test import SimpleTestCase

from prices.adapters.steam import (
    REQUEST_TIMEOUT_SECONDS,
    AdapterError,
    HttpResponse,
    build_normalized_url,
    fetch_steam_candidate,
    normalize_steam_response,
)


FIXTURES = Path(__file__).parent / "fixtures"
FETCHED_AT = datetime(2026, 8, 29, 1, 2, 3, tzinfo=UTC)


def fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


class SteamAdapterTests(SimpleTestCase):
    mapping = SimpleNamespace(
        external_product_id="1091500", region="KR", currency_expectation="KRW"
    )

    def normalize(self, name: str, *, status: int = 200):
        url = build_normalized_url("1091500")
        return normalize_steam_response(
            external_product_id="1091500",
            normalized_url=url,
            response=HttpResponse(status=status, body=fixture(name), fetched_at=FETCHED_AT),
        )

    def test_success_normalizes_only_contract_fields_and_hashes_receipt(self):
        candidate = self.normalize("steam_success.json")
        self.assertEqual(candidate.external_product_id, "1091500")
        self.assertEqual(candidate.source_title, "Cyberpunk 2077")
        self.assertEqual(candidate.currency, "KRW")
        self.assertEqual(candidate.current_amount, 33_000)
        self.assertEqual(candidate.regular_amount, 66_000)
        self.assertEqual(candidate.discount_percent, 50)
        self.assertEqual(len(candidate.response_sha256), 64)
        self.assertEqual(len(candidate.receipt_identity), 64)
        self.assertNotIn("price_overview", repr(candidate))

    def test_request_is_https_kr_korean_and_uses_finite_timeout(self):
        captured = {}

        def transport(url, timeout):
            captured.update(url=url, timeout=timeout)
            return HttpResponse(200, fixture("steam_success.json"), FETCHED_AT)

        fetch_steam_candidate(self.mapping, transport=transport)
        self.assertEqual(
            captured["url"],
            "https://store.steampowered.com/api/appdetails?appids=1091500&cc=kr&l=koreana",
        )
        self.assertEqual(captured["timeout"], REQUEST_TIMEOUT_SECONDS)

    def test_invalid_inputs_have_stable_rejection_codes(self):
        cases = [
            ("steam_wrong_currency.json", "UNSUPPORTED_CURRENCY"),
            ("steam_missing_price.json", "MISSING_CURRENT_PRICE"),
            ("steam_product_mismatch.json", "PRODUCT_ID_MISMATCH"),
            ("steam_source_failure.json", "SOURCE_PRODUCT_FAILURE"),
        ]
        for filename, code in cases:
            with self.subTest(filename=filename), self.assertRaises(AdapterError) as raised:
                self.normalize(filename)
            self.assertEqual(raised.exception.code, code)
            self.assertFalse(raised.exception.retryable)

    def test_malformed_json_and_http_failures_are_classified(self):
        url = build_normalized_url("1091500")
        with self.assertRaises(AdapterError) as malformed:
            normalize_steam_response(
                external_product_id="1091500",
                normalized_url=url,
                response=HttpResponse(200, b"{not-json", FETCHED_AT),
            )
        self.assertEqual(malformed.exception.code, "INVALID_JSON")
        with self.assertRaises(AdapterError) as unavailable:
            normalize_steam_response(
                external_product_id="1091500",
                normalized_url=url,
                response=HttpResponse(503, b"synthetic failure", FETCHED_AT),
            )
        self.assertEqual(unavailable.exception.code, "HTTP_STATUS_503")
        self.assertTrue(unavailable.exception.retryable)

    def test_network_failure_redacts_runtime_details(self):
        fake_secret = "FAKE_SECRET_SHOULD_NOT_ESCAPE"

        def timeout(_url, _timeout):
            raise TimeoutError(fake_secret)

        with self.assertRaises(AdapterError) as raised:
            fetch_steam_candidate(self.mapping, transport=timeout)
        self.assertEqual(raised.exception.code, "NETWORK_FAILURE")
        self.assertTrue(raised.exception.retryable)
        self.assertNotIn(fake_secret, str(raised.exception))

    def test_non_integer_and_impossible_discount_are_rejected(self):
        url = build_normalized_url("1091500")
        bodies = [
            b'{"1091500":{"success":true,"data":{"steam_appid":1091500,"name":"Cyberpunk 2077","price_overview":{"currency":"KRW","initial":6600000,"final":true,"discount_percent":50}}}}',
            b'{"1091500":{"success":true,"data":{"steam_appid":1091500,"name":"Cyberpunk 2077","price_overview":{"currency":"KRW","initial":6600000,"final":3300000,"discount_percent":0}}}}',
            b'{"1091500":{"success":true,"data":{"steam_appid":1091500,"name":"Cyberpunk 2077","price_overview":{"currency":"KRW","initial":6600000,"final":3299999,"discount_percent":50}}}}',
        ]
        expected = [
            "INVALID_CURRENT_AMOUNT",
            "INCONSISTENT_DISCOUNT",
            "INVALID_KRW_AMOUNT_SCALE",
        ]
        for body, code in zip(bodies, expected, strict=True):
            with self.subTest(code=code), self.assertRaises(AdapterError) as raised:
                normalize_steam_response(
                    external_product_id="1091500",
                    normalized_url=url,
                    response=HttpResponse(200, body, FETCHED_AT),
                )
            self.assertEqual(raised.exception.code, code)
