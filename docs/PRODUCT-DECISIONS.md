# Fixed product decisions

This is the starting contract for the first implementation session. A fixed
decision changes only through an explicit human decision and a dedicated commit.

## Repository and history

- Expected repository and visibility: The product uses the public repository `https://github.com/seungwoo7050/audience-foundry-game-price.git`, with `backend/`, `web/`, and `docs/` at the root. The human product owner approved this existing public remote on 2026-08-29. Normal non-force pushes to the approved `main` branch are authorized for the first implementation; public release or production deployment remains a separate checkpoint.
- Expected baseline branch and commit: The approved baseline is branch `main` at commit `3c80794c25f73aa3eed188357acd02b665e7393c`, the first commit containing the six completed contract documents and no product implementation. Remote `origin/main` was verified at the same commit before implementation on 2026-08-29.
- Legacy code/history reuse policy: No legacy implementation or history has been identified for import. Existing open-source frameworks and libraries may be added as reviewed dependencies, but competitor applications, mappings, datasets, and price histories must not be copied or presented as product-owned observations.
- External repositories that are frozen, imported, or out of scope: No external repository is approved for import or vendoring. Competitor repositories and datasets are out of scope. A dependency may be referenced through its package manager only after version, license, maintenance status, and security posture are reviewed.

## Product invariants

List statements that must remain true across every successful and failed flow.
Make each statement testable.

1. A canonical game identity is product-owned and does not use an external store identifier as its primary identity.
2. A store product maps to exactly one canonical game and one edition while that mapping is approved.
3. A store product is unique by store, external product identifier, region, and edition key.
4. Prices are stored as integer minor units with an explicit ISO currency code; floating-point values are forbidden for stored money amounts.
5. The MVP publishes only `KR`-region observations whose accepted currency is `KRW`.
6. An accepted price observation is immutable. Corrections create a new decision or observation and never rewrite audit history.
7. The current published price is derived from the latest accepted observation according to ordering rules; rejected, failed, or older out-of-order candidates cannot replace it.
8. “Observed low” means the minimum accepted current price recorded on or after the mapping’s product-owned tracking start. The public page must not label it as an all-time low.
9. A new source or source mapping cannot become active without a recorded human approval.
10. Replaying the same ingestion identity cannot create a duplicate accepted observation or duplicate external side effect.
11. A failed or interrupted ingestion cannot leave a partially updated canonical price state.
12. External requests are read-only in the MVP; the product does not change store accounts, carts, wishlists, prices, or catalog data.
13. Credentials, cookies, authorization headers, and secret values must not appear in public output, committed fixtures, or application logs.
14. All canonical timestamps are stored in UTC. Korean local time may be presented to users, but it is not the ordering source of truth.
15. Astro and any generated page are read-only consumers. They do not write directly to PostgreSQL and are not the source of truth.

## Actors and authority

- Actor identities and trust boundaries: The human product owner is the final decision authority. The MVP has one authenticated human operator trust boundary in Django Admin, one backend ingestion worker identity controlled by the product, an unauthenticated public visitor with read-only access, an Astro build or render process with read-only API access, and an external store outside the product trust boundary.
- Actions allowed for each actor: The human product owner may approve sources, mappings, destructive changes, production use, and monetization. The authenticated operator may create draft canonical records, submit or apply approved mappings, trigger ingestion, inspect failures, and reject invalid candidates. The ingestion worker may fetch only approved mappings, validate input, and write through the defined transactional service. Astro may read publishable data only. A visitor may read public pages only. The external store controls its own catalog and response.
- Human-only decisions or checkpoints: Source terms and legal acceptance; provider account creation, login, payment, 2FA, or secret entry; activation of a source; approval or correction of a product mapping; acceptance of a new dependency with material license restrictions; destructive database migration; public branding; production deployment; and any advertisement, affiliate, payment, or user-account feature.

## State model

- Initial state: The repository contains documentation only. The database begins empty. A newly created canonical game is `DRAFT`; a source mapping is `DRAFT`; no price is publishable; and no source is active until its human approval is recorded.
- Allowed transitions and actors: A human operator may move a mapping from `DRAFT` to `APPROVED`, `REJECTED`, or later `PAUSED`; only `APPROVED` mappings may be ingested. The worker moves an ingestion run from `QUEUED` to `RUNNING`, then to `SUCCEEDED`, `FAILED_RETRYABLE`, or `FAILED_FINAL`. A candidate observation moves from `RECEIVED` to `ACCEPTED`, `REJECTED`, or `DUPLICATE`. Acceptance writes the immutable observation, current-price projection, and execution audit in one transaction. A human may suspend publication without deleting history.
- Terminal, retryable, rejected, and partial-failure states: `SUCCEEDED`, `FAILED_FINAL`, `REJECTED`, and `DUPLICATE` are terminal for a specific run or candidate. `FAILED_RETRYABLE` may be retried with the same idempotency identity. Validation failures are rejected and require corrected input or a human mapping decision. A partial external read or partial local write is never publishable; the canonical transaction rolls back, while the failed run and redacted failure evidence remain available for diagnosis.

## First implementation sequence

Order the smallest capabilities needed to close the first loop. Put the riskiest
interface viability check before expanding dependent implementation.

1. Record the exact live source request shape, terms checkpoint, accepted fields, response hash method, and failure behavior for one human-selected Steam product. Stop live work if the source cannot be approved.
2. Use the approved Python, Node.js, package-manager, and PostgreSQL versions to create reproducible lockfiles before the first migration.
3. Create the canonical entities, database constraints, UTC timestamp policy, and additive initial migrations.
4. Configure Django Admin and authentication for the single operator role without custom public administration UI.
5. Implement the source adapter against deterministic fixtures, including invalid currency, missing price, timeout, duplicate, and out-of-order cases.
6. Implement one manually triggered ingestion service with transaction, idempotency, validation, audit evidence, current-price derivation, and observed-low derivation.
7. Define and verify the read-only `/api/v1` game-price contract. Astro must not access PostgreSQL directly.
8. Implement the smallest Astro game page and title lookup needed to display the accepted state and observation scope.
9. Run the local closed loop, the separately approved live read-only viability spike, negative scenarios, and manual acceptance. Production deployment remains deferred.

## Explicit non-goals

- Importing or reconstructing price history from a competitor.
- Covering the entire Steam catalog or more than one store.
- Automatically deciding that two differently named products or editions are equivalent.
- Running unattended scheduled collection or a distributed job queue.
- Providing user accounts, wishlists, email alerts, payments, subscriptions, affiliate redirects, advertisements, or personalized recommendations.
- Building a custom administrator application when Django Admin is adequate.
- Allowing Astro or browser code to mutate canonical data.
- Claiming production readiness, legal clearance, search traffic, revenue, scale, or all-time price coverage from the MVP.
- Deploying to production or performing a destructive migration during the documentation or first local acceptance stage.

## Decision-change policy

Describe who may change fixed decisions and what evidence is required.

Only the human product owner may change a fixed product decision. Each change requires a dedicated commit that identifies the old decision, the new decision, the reason, affected invariants and acceptance scenarios, data migration or rollback consequences, source or license evidence when applicable, and whether previously accepted observations remain valid. Implementation convenience alone is not evidence. No agent or dependency upgrade may silently widen scope, activate a source, change data ownership, weaken auditability, or reinterpret “observed low.”
