import { readFile } from "node:fs/promises";

const html = await readFile(
  new URL("../dist/games/cyberpunk-2077/index.html", import.meta.url),
  "utf8",
);

const expectedPath = process.env.GAMEPRICE_EXPECTED_API_JSON;
const expected = expectedPath
  ? JSON.parse(await readFile(expectedPath, "utf8"))
  : {
      game: { title: "Cyberpunk 2077" },
      price: {
        edition: { label: "Standard Edition" },
        source: { name: "Steam" },
        currency: "KRW",
        region: "KR",
        current_amount_minor: 33000,
        observed_low_amount_minor: 33000,
        observed_low_label: "추적 시작 이후 관찰된 최저가",
      },
    };
const money = new Intl.NumberFormat("ko-KR", {
  style: "currency",
  currency: expected.price.currency,
  maximumFractionDigits: 0,
});
const required = [
  expected.game.title,
  expected.price.edition.label,
  expected.price.source.name,
  money.format(expected.price.current_amount_minor),
  money.format(expected.price.observed_low_amount_minor),
  expected.price.observed_low_label,
  "역대 최저가를 뜻하지 않습니다",
  `${expected.price.currency} / ${expected.price.region}`,
];
for (const value of required) {
  if (!html.includes(value)) throw new Error(`RENDER_ASSERTION_MISSING:${value}`);
}
for (const value of ["FAKE_SECRET_SHOULD_NOT_ESCAPE", "idempotency_key", "receipt_identity"]) {
  if (html.includes(value)) throw new Error(`RENDER_EXPOSED_INTERNAL_VALUE:${value}`);
}
console.log(`render assertions passed: ${required.length} required, 3 forbidden`);
