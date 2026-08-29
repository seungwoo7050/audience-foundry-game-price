# Audience Foundry Scaffold

Audience Foundry Scaffold is a domain-neutral starting repository for building a
new product with an AI coding agent. It contains development policy, security
boundaries, decision templates, acceptance-evidence templates, and one reusable
first implementation prompt. It intentionally contains no product implementation.

The scaffold separates three kinds of material:

1. **Universal rules** stay in every derived repository: reviewable commits,
   evidence-backed validation, safe Git practice, secret handling, dependency
   provenance, and honest completion reporting.
2. **Conditional patterns** are adopted only when the domain needs them:
   approvals, immutable inputs, audit events, idempotency, adapters, migrations,
   and local-first provider simulations.
3. **Domain decisions** must be written for each product: users, problem, data,
   state model, external boundaries, technology, MVP loop, risks, and non-goals.

Do not begin implementation by treating a template as a product decision. Follow
[`docs/ADOPTION-GUIDE.md`](docs/ADOPTION-GUIDE.md), use the reusable
[`domain-documentation prompt`](docs/templates/DOMAIN-DOCUMENTATION-PROMPT.md) in
the business-design conversation, review and commit the resulting project
documents, and then give the implementation agent
[`prompts/FIRST-IMPLEMENTATION-PROMPT.md`](prompts/FIRST-IMPLEMENTATION-PROMPT.md)
without modification.

## Repository contents

- [`DEVELOPMENT-RULES.md`](DEVELOPMENT-RULES.md): portable commit and validation policy
- [`SECURITY-AND-OPERATIONS.md`](SECURITY-AND-OPERATIONS.md): portable safety boundary
- [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md): dependency provenance baseline
- [`docs/PORTABILITY-MAP.md`](docs/PORTABILITY-MAP.md): what is universal or variable
- [`docs/ADOPTION-GUIDE.md`](docs/ADOPTION-GUIDE.md): short preparation workflow
- `docs/templates/`: documents to copy and complete for a chosen domain
- `prompts/`: the reusable agent handoff prompt

## Baseline status

This root scaffold claims only that its policy and templates exist. It does not
claim that a product, dependency graph, runtime, account, deployment, database,
credential, domain name, or external provider has been selected or created.

The repository is private by default. A derived product must make an explicit
licensing and visibility decision before redistribution or public release.
