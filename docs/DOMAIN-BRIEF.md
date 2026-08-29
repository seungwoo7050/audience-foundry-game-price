# Domain brief

## Product identity

- Working name: **GamePrice KR** (provisional public name; suggested repository slug: `game-price-kr`).
- One-sentence product: A Korean-language PC-game price site that records approved KRW price observations from selected stores and shows the current price and the lowest price observed since this product began tracking it.
- Business owner or decision maker: The human product owner. Only the human product owner may approve data-source terms, change fixed scope, authorize production use, or introduce monetization.

## Customer and problem

- First customer segment: Korean PC gamers deciding whether to buy a digitally distributed PC game now or wait for a lower price.
- Primary user and actor roles: An anonymous public visitor reads price information; an authenticated human operator approves sources and product mappings; an ingestion worker fetches and validates source data; an external store owns the upstream product and price representation.
- Painful job or unmet need: The user must determine the Korean selling price, the applicable edition and region, and whether the current discount is low relative to prices observed over time.
- Current workaround and its cost: Users visit multiple store pages or foreign-language comparison services and manually reconcile titles, editions, regions, currencies, and historical-price claims. This costs time and can produce a comparison between different products or unsupported claims about an all-time low.
- Why this is worth solving now: The first loop can be tested with one approved store, a small operator-selected catalog, and a product-owned observation history. The expectation of Korean search traffic is a testable business assumption, not a verified fact.

## First closed loop

Describe one user-visible sequence from trusted input to durable outcome. It must
be small enough to prove locally or in an approved sandbox.

1. The human product owner approves one read-only store interface for a limited viability test and approves one mapping between a canonical game and one Korean-region store product.
2. The operator triggers a single ingestion run for that approved mapping.
3. The Django backend fetches the source response, validates the product identity, region, currency, and price fields, records an immutable receipt identity, and either rejects the candidate or commits one accepted price observation and its audit evidence in one transaction.
4. The Django read interface exposes only accepted, publishable data.
5. Astro consumes that versioned read contract and produces a public game page.
6. A visitor opens the page and sees the canonical game name, current KRW price, lowest price observed since tracking began, source, and observation time.

The durable outcome is the accepted price observation, its provenance and audit record, and a public page derived from that accepted state. A generated Astro page is a presentation artifact, not the source of truth.

## Success measures

State measurable MVP outcomes and unacceptable failures.

- Success: One approved store product completes the loop using deterministic local fixtures, and the same adapter completes one separately approved live read-only viability request. The public page values match the accepted database observation exactly; replaying the same input creates no duplicate price observation; and the page explicitly labels the low as “lowest observed since tracking began.”
- Unacceptable failure: Publishing a price for the wrong game, edition, region, or currency; claiming an all-time historical low without owned evidence; allowing rejected or stale input to replace the latest accepted price; leaving a partial canonical write after failure; exposing a credential; or collecting live data before the required human source-terms checkpoint.

## Scope

- MVP capabilities: A small operator-selected catalog; canonical game and store-product records; one approved Korean-region price-source adapter; manual mapping approval; manually triggered ingestion; validation and rejection; immutable accepted price observations; current-price and observed-low derivation; Django Admin for operator work; one versioned read-only JSON contract; and Astro public pages with basic title lookup or direct game navigation.
- Explicit non-goals: Whole-store catalog ingestion, multiple stores, imported historical prices, competitor API or dataset dependence, automatic product matching, user accounts, wishlists, price alerts, payments, advertisements, affiliate redirects, newsletters, native applications, complex dashboards, production deployment, and unattended scheduled collection.
- Later possibilities that must not shape the first implementation: Additional stores, automated matching, full-text search, user watchlists, email alerts, affiliate revenue, advertisements, public data downloads, multiple public sites, recommendation features, and continuous scheduling.

## Domain language

Define important terms, avoiding synonyms for distinct concepts.

- **Canonical game:** The product-owned identity for one game, independent of any store listing.
- **Store:** An external seller or platform that owns its own catalog and price representation.
- **Store product:** One store-specific purchasable listing, identified by the store, external product identifier, region, and edition.
- **Edition:** The product composition represented by a store product, such as base, deluxe, bundle, or downloadable content. Distinct editions must not be compared as the same product.
- **Source mapping:** The operator-approved relationship from a store product to a canonical game and edition.
- **Price observation:** An immutable, accepted record of a store product’s normalized price state at a known observation time.
- **Current price:** The amount from the latest accepted observation that is eligible for publication.
- **Observed low:** The minimum accepted current-price amount recorded by this product on or after the mapping’s tracking start. It is not an all-time market claim.
- **Source receipt:** Minimal immutable evidence identifying the external request and response, including hashes and timestamps, without retaining secrets or unnecessary source content.
- **Ingestion run:** One attempt to fetch, validate, and apply source data for an approved mapping.
- **Verification decision:** An immutable human approval or rejection of a source, mapping, or exceptional data candidate.
- **Published price:** A derived read model created only from accepted observations.

## Facts, assumptions, and open questions

- Verified facts: The selected architecture is Django plus Astro with PostgreSQL persistence. The fixed version families are Python 3.12, Django 5.2 LTS, and Astro 7. The product must own its canonical mappings, accepted price observations, provenance, and operating rules while using existing framework capabilities for general web, administration, persistence, and presentation functions. The first product direction is a Korean PC-game current-price and observed-low site, and competitor datasets or imported competitor price history are not required for the first loop.
- Assumptions to test: Korean users will search for and repeatedly use Korean-region game-price pages; a human-approved Steam price interface will permit the limited retrieval and storage needed by the MVP; one-store coverage is sufficient to test user value; manual mapping remains manageable for the first catalog; and source identifiers and price fields remain stable enough to isolate behind an adapter.
- Open questions that do not block implementation: Final public brand and domain; remote repository URL and visibility; exact PostgreSQL major version; Python and JavaScript package-manager choice; hosting provider; collection cadence after the MVP; business traffic threshold; monetization providers; and long-term retention periods for noncanonical operational logs. Live external acceptance remains gated on human approval of the chosen source interface and its terms, but deterministic local implementation can proceed before that checkpoint.
