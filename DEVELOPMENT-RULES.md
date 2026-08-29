# Development rules

These rules apply to hand-authored work in every repository derived from Audience
Foundry Scaffold. Project-specific invariants belong in `docs/PRODUCT-DECISIONS.md`.

## Priority

Apply requirements in this order:

1. safety, security, law, privacy, and license obligations
2. explicit user intent and approved project decisions
3. correctness, integrity, and compatibility
4. verifiable delivery and rollback boundaries
5. commit-size conventions

Never weaken correctness or safety to make a commit smaller or faster.

## Readiness before implementation

Read every required project document from beginning to end. Do not implement while
a required decision is absent, contradictory, or still marked `TODO(required)`.
Resolve material uncertainty in a decision document before code encodes it.

Verify the repository identity, expected starting commit, origin, visibility,
branch, clean state, legacy-reuse policy, and external-system readiness recorded by
the project. Do not assume accounts, credentials, production identifiers, migrated
state, or compatibility that was not verified.

## Plan by reviewable atoms

Before implementation, decompose work into the smallest complete changes that are
independently explainable, testable, reviewable, and revertible. Each commit answers
one primary review question.

Implementation and the smallest focused tests required to prove it normally belong
in the same commit. Formatting, dependency updates, generated output, vendored or
mechanically imported code, and unrelated cleanup belong in separate commits.

For each planned atom, record:

- purpose and primary review question
- dependencies and expected files
- focused validation and acceptance evidence
- rollback boundary
- expected meaningful churn and any size exception

## Commit size

For hand-authored changes, target 20–80 meaningful lines and one or two primary
production files.

Reconsider the boundary above 100 meaningful lines or three primary files. Split
by default above 150 meaningful lines. A commit above 200 meaningful lines or five
primary files requires a concrete explanation of why validation and rollback are
inseparable.

These are review warnings, not hard CI failures. Lockfiles, generated output,
mechanically imported upstream source, and formatting-only churn do not count as
hand-authored meaningful lines, but must be isolated and have provenance recorded.
The initial policy/template root commit is an explicit scaffold exception.

## Commit messages and history

Use an imperative Conventional Commit subject with a narrow scope, for example:

```text
docs(domain): define the first customer loop
build(deps): pin the validation toolchain
feat(order): reject duplicate fulfillment
fix(audit): couple the event to its receipt
```

The body states the reason, focused validation, and any non-obvious rollback or
size exception. Never invent test claims. Do not rewrite pushed history,
force-push, or delete branches without explicit authorization.

## Validation

Run the narrowest relevant check while developing and the repository gate before
publishing a completed series. Record exactly what ran and distinguish automated
evidence, simulated evidence, and manual acceptance.

Never mark a gate as passing when it was skipped, unavailable, run against another
commit, or used a mock where live integration was required. Pin external inputs and
identify exact revisions in evidence when reproducibility depends on them.

Security, authorization, data-integrity, destructive-migration, secret-exposure,
idempotency, audit-atomicity, and external-interface incompatibility defects block
forward implementation. Cosmetic and report-only cleanup may be batched after the
functional loop closes.

## Dependencies and external systems

- Prefer reviewed, exact-version dependencies over copying or forking upstream.
- Keep dependency, import, vendor, and generated churn separate from behavior.
- Preserve upstream licenses, notices, integrity metadata, and source provenance.
- Define external systems through owned interfaces, not internal implementation.
- Prove a risky interface with the smallest real viability spike before expanding.
- Never inspect or import legacy implementation unless project decisions explicitly
  authorize its role, scope, provenance, and migration evidence.

## Working tree discipline

- Preserve unrelated user changes in a dirty worktree.
- Use reversible changes and non-destructive Git operations.
- Keep credentials and runtime secrets outside Git.
- Do not modify a frozen or externally owned repository unless explicitly scoped.
- Stop at account login, payment, 2FA, production secret, legal acceptance, or
  other human-only checkpoints rather than fabricating values or consent.

## Completion evidence

A completed feature reports:

- exact commit SHA, branch, origin, and clean/dirty state
- focused checks and full gates actually run
- acceptance scenarios and their evidence type
- security, privacy, license, migration, compatibility, and integrity implications
- external state changed and how it can be recovered or rolled back
- manual checkpoints, known risks, blockers, and deferred work

Documentation and reports describe the repository and external state as verified,
not as intended.
