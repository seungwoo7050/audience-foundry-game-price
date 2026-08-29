import { readFile } from "node:fs/promises";

const html = await readFile(
  new URL("../dist/games/cyberpunk-2077/index.html", import.meta.url),
  "utf8",
);

const required = [
  "Cyberpunk 2077",
  "Standard Edition",
  "Steam",
  "₩33,000",
  "추적 시작 이후 관찰된 최저가",
  "역대 최저가를 뜻하지 않습니다",
  "KRW / KR",
];
for (const value of required) {
  if (!html.includes(value)) throw new Error(`RENDER_ASSERTION_MISSING:${value}`);
}
for (const value of ["FAKE_SECRET_SHOULD_NOT_ESCAPE", "idempotency_key", "receipt_identity"]) {
  if (html.includes(value)) throw new Error(`RENDER_EXPOSED_INTERNAL_VALUE:${value}`);
}
console.log(`render assertions passed: ${required.length} required, 3 forbidden`);
