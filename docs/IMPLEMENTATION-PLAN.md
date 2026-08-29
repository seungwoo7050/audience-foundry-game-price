# Implementation plan

This plan implements the first GamePrice KR loop approved on 2026-08-29. Each
atom has one primary review question and an independently revertible boundary.

| Atom | Review question and purpose | Expected files/dependencies | Focused proof | Rollback boundary | Status |
| --- | --- | --- | --- | --- | --- |
| 0 | Are repository, runtime, license, and live-source decisions explicit before code? | `docs/DOMAIN-BRIEF.md`, `docs/PRODUCT-DECISIONS.md`, `docs/TECHNOLOGY-DECISIONS.md`; human approval for Psycopg 3.3.4 and Steam App ID 1091500 | Clean baseline; local and remote SHA; approval record in implementation history | Revert before dependent atoms | completed |
| 1 | Is the MVP decomposed into reviewable, evidence-backed changes? | This plan only | Required fields complete; no unresolved required placeholder | Revert this documentation commit | completed |
| 2 | Can both applications install reproducibly on the approved runtimes? | `backend/pyproject.toml`, `backend/uv.lock`, `web/package.json`, `web/package-lock.json`, runtime pins, `THIRD_PARTY_NOTICES.md` | Frozen installs; version and license metadata; advisory checks | Remove manifests, locks, and installed environments | completed |
| 3 | Does PostgreSQL enforce the canonical identity, money, approval, immutability, and audit schema? | Django project, price models, Admin registration, initial migration, model tests | Django checks; empty PostgreSQL migration; constraint, authority, and immutability tests | Reverse the additive initial migration or drop the disposable database | completed |
| 4 | Does the Steam adapter accept only the approved response shape and redact failures? | Adapter, deterministic minimized fixtures, adapter tests | Success, malformed JSON, source failure, timeout, mismatch, region/currency, money, discount, and secret-redaction tests | Revert adapter and synthetic fixtures; no canonical data affected | completed |
| 5 | Does one transactional ingestion service preserve idempotency, ordering, audit atomicity, retry, and rollback? | Ingestion service, management command, focused integration tests | Positive, replay, duplicate, out-of-order, retryable failure, injected partial-write failure, and concurrent-request tests with exact row counts | Revert service/command; schema remains compatible and observations are append-only | completed |
| 6 | Is the public `/api/v1` projection read-only, minimal, and contract-stable? | Django URL/view, checked-in contract fixture, API tests | Exact response fixture, 404/unpublished tests, method rejection, no confidential fields | Revert API files without changing canonical state | planned |
| 7 | Does Astro render the exact accepted state and correctly scope the observed low? | Astro configuration, TypeScript contract, game page, lookup page, styles, render assertions | Astro check/build; saved HTML assertions for title, amounts, source, time, edition, and “tracking began” wording | Revert `web/src`; generated output is rebuildable | planned |
| 8 | Can a clean checkout reproduce the complete fixture loop and all required gates? | Repository gate script/Makefile, local PostgreSQL runner, README, secret/license/schema checks | Frozen installs, empty migration, full backend tests, fixture ingestion, API export, Astro check/build, generated-output scan, clean-state precheck | Revert developer tooling; behavior commits remain independently testable | planned |
| 9 | Does the approved live Steam interface work through the same adapter and remain idempotent? | Redacted local evidence and completion-report inputs; no raw response fixture | One read-only request for App ID 1091500, response SHA-256, normalized KRW fields, stored observation, API/Astro render, replay result | Remote read has no rollback; delete disposable local DB and rebuild the site | planned |
| 10 | Are completion claims tied to the exact final commit and honestly scoped? | `docs/COMPLETION-REPORT.md`, plan status updates, final verification | Full gate on closure commit, local/remote SHA equality, branch/origin, clean worktree | Revert report only; functional commits remain | planned |

## Ordering rationale

The approved decisions and plan precede all code. Dependency and generated lock
churn is isolated before behavior. The additive schema establishes owned
identities and database constraints before adapters or services depend on them.
Synthetic adapter proof precedes network use; transactional failure paths land
with ingestion before any end-to-end publication claim. The API contract precedes
Astro so the browser never becomes authoritative. Reproducible gates run before
the separately approved live viability request. Closure records only evidence
actually produced by the exact commits under review.

## Size exceptions

Atom 2 includes generated lockfiles whose line count is not meaningful hand-authored
churn. Atom 3 may exceed 200 lines across models, migration, Admin, and tests because
the initial relational constraints must be reviewed and rolled back as one schema
contract. Atom 5 may exceed 200 lines because transaction, idempotency, audit event,
fault injection, and their integration proof are inseparable. Atom 7 may exceed the
usual limit because the first Astro shell, route, contract type, and render proof
form one independently buildable presentation boundary. Generated migrations and
site output are excluded from hand-authored size counts.

## Blocking findings

Psycopg 3.3.4 (`LGPL-3.0-only`) and the one read-only Steam request for App ID
1091500 (`Cyberpunk 2077`, `Standard Edition`, `KR`) were explicitly approved by
the human product owner on 2026-08-29. No login, credential, payment, 2FA,
production deployment, destructive migration, or external mutation is authorized.
Any secret exposure, non-KRW response, product mismatch, transaction leak, or
unstable live interface stops the dependent acceptance claim and is reported as
unproved rather than replaced by simulation.
