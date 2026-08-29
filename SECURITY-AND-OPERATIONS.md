# Security and operations boundary

This file defines portable defaults. A derived product adds its domain-specific
threats, data classes, authorization model, retention, and regulatory obligations
to the project decision documents.

## Default security posture

- Treat all credentials, session material, recovery data, personal data, provider
  identifiers, and production configuration as sensitive until classified.
- Never commit secrets or place them in content, fixtures, test snapshots, logs,
  prompts, audit events, receipts, generated artifacts, or documentation.
- Refer to secret environment-variable names in configuration; inject values only
  at runtime through an approved interactive or managed-secret procedure.
- Redact external error bodies and command output before persisting or reporting.
- Use least privilege and local or disposable environments before real providers.
- Reject insecure remote transport; document justified loopback-only exceptions.
- Do not invent accounts, identities, domains, resource IDs, user consent, or
  production readiness.

## Human checkpoints

Stop before login, payment, billing acceptance, 2FA, recovery-code handling,
password or token entry, production deployment, destructive migration, legal terms,
or contacting another person unless the user explicitly authorizes that exact step.
Do not ask the user to paste sensitive values into chat or commit them to a file.

## Data and authorization

Before implementing data storage or a state-changing operation, the project must
define:

- data owner, classification, source of truth, and retention/deletion policy
- actor identities, trust boundaries, and authorization checks
- state invariants and who may cause each transition
- audit requirements and separation of decision from execution when applicable
- replay, concurrency, idempotency, partial-failure, and recovery behavior
- backup, rollback, migration, and compatibility expectations

If a category is not applicable, record why rather than silently omit it.

## External changes

Resolve exact targets with read-only checks before mutation. Constrain external
actions to resources named by the project. Prefer preview, draft, sandbox, dry-run,
or reversible state. Report what changed and whether it is recoverable.

Account availability, credentials, quotas, billing, network access, and provider
capabilities are unverified until checked. Their absence is a blocker, not permission
to substitute a different provider or weaken a gate.

## Supply chain and licensing

Pin direct dependencies, commit integrity locks, review registry metadata, retain
notices, and keep copied or generated source provenance explicit. A dependency
audit does not replace license review. Do not claim zero risk when only a subset of
the dependency graph was audited.
