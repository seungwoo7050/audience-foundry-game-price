export interface GamePriceV1 {
  schema_version: 1;
  game: {
    id: string;
    slug: string;
    title: string;
  };
  price: {
    store_product_id: string;
    source: { code: string; name: string };
    edition: { key: string; label: string };
    region: "KR";
    currency: "KRW";
    current_amount_minor: number;
    regular_amount_minor: number | null;
    discount_percent: number | null;
    observed_low_amount_minor: number;
    observed_low_scope: "SINCE_TRACKING_BEGAN";
    observed_low_label: string;
    tracking_started_at: string;
    latest_observed_at: string;
  };
}

function assertContract(value: unknown): asserts value is GamePriceV1 {
  if (!value || typeof value !== "object") throw new Error("API_CONTRACT_INVALID");
  const response = value as Partial<GamePriceV1>;
  const game = response.game;
  const price = response.price;
  if (
    response.schema_version !== 1 ||
    !game ||
    typeof game.id !== "string" ||
    typeof game.slug !== "string" ||
    typeof game.title !== "string" ||
    !price ||
    price.region !== "KR" ||
    price.currency !== "KRW" ||
    price.observed_low_scope !== "SINCE_TRACKING_BEGAN" ||
    !Number.isSafeInteger(price.current_amount_minor) ||
    !Number.isSafeInteger(price.observed_low_amount_minor) ||
    typeof price.latest_observed_at !== "string" ||
    typeof price.tracking_started_at !== "string"
  ) {
    throw new Error("API_CONTRACT_INVALID");
  }
}

export async function getGamePrice(slug: string): Promise<GamePriceV1> {
  const base =
    import.meta.env.GAMEPRICE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
  const url = `${base.replace(/\/$/, "")}/games/${encodeURIComponent(slug)}/`;
  const response = await fetch(url, { signal: AbortSignal.timeout(5_000) });
  if (!response.ok) throw new Error(`API_READ_FAILED_${response.status}`);
  const payload: unknown = await response.json();
  assertContract(payload);
  return payload;
}
