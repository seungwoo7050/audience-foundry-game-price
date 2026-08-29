# Portability map

Publisher proved that a small implementation can close a valuable loop when the
decision space is constrained before coding. This map prevents its domain choices
from being mistaken for universal architecture.

## Always carry forward

- priority order: safety and intent before speed or commit size
- decision documents before implementation
- reviewable, testable, revertible commit atoms
- focused tests with behavior and a full gate at completion
- exact evidence, immutable revisions, honest skipped/blocker reporting
- clean Git discipline and preservation of unrelated work
- dependency pinning, provenance, licensing, and generated-churn isolation
- secrets outside Git, prompts, logs, fixtures, receipts, and artifacts
- explicit human checkpoints for accounts, money, credentials, and destructive state
- external interfaces and ownership boundaries documented before integration
- smallest real viability spike for high-risk compatibility
- completion reports that state actual repository and external state

## Carry forward only when the domain needs it

- immutable approval: use when a human decision must bind to exact input
- separate decision/execution events: use when authorization and action need audit
- idempotency keys and receipts: use for retryable external side effects
- adapter architecture: use when one domain operation has multiple external engines
- Git-backed state: use for reviewable low-volume artifacts, not by default for all data
- local provider simulation: use when it faithfully exercises the production boundary
- append-only audit: use when traceability or regulated state transitions require it
- migration/rollback gates: strengthen them when existing durable data is involved

Each adopted conditional pattern must be justified in `PRODUCT-DECISIONS.md` and
made testable in `MVP-ACCEPTANCE.md`.

## Decide again for every product

- customer, buyer, user, actor, and permissions
- problem, value proposition, workflow, and measurable outcome
- canonical entities, identities, schemas, lifecycle, and source of truth
- domain invariants, approval requirements, audit semantics, and retention
- external systems, providers, interface revisions, ownership, and failure policy
- runtime, language, framework, storage, deployment, and test technology
- regulatory, privacy, licensing, accessibility, localization, and availability needs
- legacy-system reuse or migration policy
- MVP loop, non-goals, rollout boundary, and completion evidence

Publisher-specific Markdown, Decap, Public Sites, WordPress, article/site/engine
model, draft policy, commit-bound publication approval, and release/build-report
contract belong to this last category. They are examples, not scaffold defaults.
