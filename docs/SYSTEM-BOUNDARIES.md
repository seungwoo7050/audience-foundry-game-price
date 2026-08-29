# System boundaries

## Ownership

- Data and behavior this product owns: Canonical game identities; store and store-product identities used by this product; approved mappings between external products, editions, and canonical games; tracking-start timestamps; accepted KRW price observations collected after tracking starts; current-price and observed-low derivation rules; source receipts and audit evidence; validation, rejection, idempotency, publication, and operator-approval rules; and the public Korean presentation derived from accepted data.
- Data and behavior owned by users: The MVP has no end-user account or submitted user content. The human operator owns the decision to approve a source or mapping and controls the operator account credentials. A public visitor controls only the browser request and navigation; a visit does not grant mutation authority.
- External or frozen systems: Steam owns its catalog, product identifiers, storefront content, regional availability, price representation, interface behavior, account rules, and terms. Python, Django, Astro, Node.js, PostgreSQL, and reviewed packages remain externally maintained dependencies. The generated public page is derived and may be rebuilt; it is not canonical data.
- Systems explicitly outside the MVP: Competitor price databases and APIs, other game stores, payment processors, affiliate networks, advertising systems, email providers, analytics vendors, search-as-a-service, user identity providers, mobile applications, browser extensions, external job queues, and production hosting automation.

## Context and data flow

Describe the first loop as ordered trust-boundary crossings. Identify the source of
truth at every step.

1. **Human decision boundary:** The human product owner reviews the proposed source interface and records approval or rejection. The product audit record is the source of truth for that authority decision.
2. **Operator boundary:** The authenticated operator creates one canonical game and one draft store product, then approves the mapping and region/edition interpretation. PostgreSQL is the source of truth for the approved mapping; the external title string alone is not authoritative.
3. **External read boundary:** A manually triggered Django ingestion worker sends one read-only request for the approved external product. The external response is the source of the candidate price data only. It does not directly change canonical state.
4. **Validation boundary:** Django checks the approved mapping, response identity, region, currency, numeric constraints, ordering, and duplicate identity. The product’s validation rules are authoritative for acceptance or rejection.
5. **Transactional persistence boundary:** Django commits the accepted observation, current-price projection, and execution audit atomically in PostgreSQL. PostgreSQL becomes the source of truth for publishable state.
6. **Internal read boundary:** Astro reads only the versioned Django `/api/v1` response. The API response is a projection of PostgreSQL and cannot authorize mutation.
7. **Public boundary:** Astro renders or builds the Korean public page. The page must show the source and observation scope. If the page disagrees with PostgreSQL, the page is stale or incorrect and must be regenerated; it never overrides canonical data.

## External interfaces

For each interface, complete one entry.

### Steam Store public product-price interface

- Owner and exact version/revision: Valve/Steam owns the interface. The proposed MVP request is the unversioned public Store endpoint pattern `GET https://store.steampowered.com/api/appdetails?appids={steam_app_id}&cc=kr&l=koreana`. It is not treated as a documented stable business contract. Its usable revision must be identified at the viability checkpoint by the exact normalized request, UTC timestamp, HTTP status, accepted response-field set, response SHA-256, and implementation commit SHA.
- Input contract: One operator-approved numeric Steam application identifier per request, explicit country code `kr`, and Korean locale. The adapter must not discover or expand into unrelated products in the first loop.
- Output contract: JSON keyed by the requested application identifier. The adapter may accept only a successful product response whose verified field set identifies the requested product and provides an integer current amount, an explicit currency equal to `KRW`, an optional integer regular amount, and an optional bounded discount percentage. Every accepted field is normalized into the product schema; unrecognized fields are ignored rather than copied wholesale.
- Authentication and secret boundary: The proposed public request assumes no Steam session cookie, personal account, or embedded credential. If login, API key, consent, payment, 2FA, or a privileged account becomes necessary, implementation must stop for the human checkpoint. Browser cookies and operator credentials must never be forwarded.
- Error and timeout behavior: A network timeout, non-success HTTP response, invalid JSON, source-level failure, missing required field, non-KRW currency, invalid amount, or product-identity conflict produces a failed or rejected run. The last accepted published price remains unchanged. Every network call must have a finite configured timeout; the exact values are pinned during the viability spike and may not be omitted.
- Retry/idempotency behavior: The MVP performs no unattended retry. The operator may retry a retryable failure with the same ingestion idempotency identity. Replaying the same response or normalized price state must produce `DUPLICATE` or refresh only noncanonical last-checked metadata; it must not create a second accepted price observation.
- Smallest real viability proof: After the human approves the interface and terms, make one live read-only request for one approved application identifier, record the redacted request metadata and response hash, validate the required KRW fields, store one observation, and verify that a repeated request is idempotent. Bulk retrieval is not part of this proof.
- Mutation and rollback boundary: The remote operation is read-only and has no remote rollback. All local canonical changes occur in one PostgreSQL transaction. On validation, audit, or persistence failure, the canonical transaction rolls back and the previous published price remains intact; the redacted failed-run record may remain.

### Product-owned read API v1

- Owner and exact version/revision: GamePrice KR owns the contract. The first revision is `/api/v1`, and its exact response is identified by a checked-in contract fixture plus the backend commit SHA. A breaking response change requires a new API version or an explicit contract migration.
- Input contract: Read-only HTTP `GET` by canonical game slug or stable game identifier, with optional basic title lookup limited to publishable games. The client cannot pass a source payload, price amount, mapping decision, or mutation command.
- Output contract: JSON containing the canonical game identity and title, publishable store product identity and edition label, region, currency, current amount in minor units, optional regular amount and discount, observed-low amount, tracking-start timestamp, latest observation timestamp, source name, and an explicit observed-low scope label. Internal confidence values, rejected candidates, credentials, raw source payloads, and operator notes are excluded.
- Authentication and secret boundary: The MVP public read contract requires no end-user login and grants no write authority. Django Admin authentication is on a separate route and trust boundary. Database credentials and source configuration remain server-side environment secrets.
- Error and timeout behavior: Unknown or unpublished games return `404`; an unavailable canonical datastore returns a non-success service response without fabricated or cached-as-current data. Astro must preserve the last successful static artifact only if it is visibly timestamped; it may not relabel stale data as newly observed.
- Retry/idempotency behavior: `GET` is safe and idempotent. Astro may retry only reads according to a finite build or render timeout. Retries do not create audit events or mutate canonical state.
- Smallest real viability proof: Against an isolated local PostgreSQL database, accept one fixture observation, request the exact `/api/v1` game response, validate it against the checked-in contract fixture, and render the Astro page whose displayed values equal the API values.
- Mutation and rollback boundary: The interface has no mutation. Rollback means serving the prior compatible backend/API revision or rebuilding the prior Astro revision. Canonical database rollback remains governed by Django migrations and data-migration policy.

## Provider and account readiness

List what has been verified and where implementation must stop for login, payment,
2FA, legal acceptance, credentials, production identifiers, or user consent.

- No Steam account, API credential, production identifier, paid plan, affiliate relationship, or legal acceptance has been verified by these documents.
- The public price endpoint’s technical response and permitted storage/use are assumptions until the human-approved live viability checkpoint is completed. Local fixture implementation may proceed, but live collection, bulk access, and production use must stop at that checkpoint.
- The official Steam `IStoreService/GetAppList/v1` catalog interface is not required for the first loop. If later used, it requires a Web API key and therefore a separate human credential checkpoint.
- The MVP does not require end-user consent, payment, subscriptions, advertising, affiliate tracking, email delivery, or public user registration.
- Operator account creation and first secret entry are human actions. Secrets must be injected outside version control.
- Production domain, TLS termination, hosting account, backup target, monitoring account, and deployment credentials are not selected and are deferred from MVP acceptance.

## Legacy and migration boundary

State whether legacy implementation, data, contracts, and runtime state may be
read, imported, migrated, or must remain untouched.

No legacy application, database, runtime state, or contract is approved for import. The first database starts empty and the product’s observation history starts when each mapping is approved. Competitor price history, mappings, and user data must remain untouched and must not be represented as product-owned history. Future imports require a separate human decision, documented source rights, provenance-preserving import rules, dry-run evidence, and rollback or rejection behavior. Open-source packages may be installed as dependencies after review; their repositories are not copied into the product history unless a separate vendoring decision is made.
