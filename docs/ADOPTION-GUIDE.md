# Adoption guide

Use the scaffold to start a new domain in five short stages.

## 1. Create an unrelated product repository

Create a new private repository from this template. Preserve the scaffold as the
root baseline, then rename the product in `README.md`. Record the expected origin,
visibility, branch, and baseline SHA in the new product decisions. Do not preserve
another product's implementation history as an accidental dependency.

## 2. Copy the required templates

In the conversation where the business and domain were decided, give the agent
[`templates/DOMAIN-DOCUMENTATION-PROMPT.md`](templates/DOMAIN-DOCUMENTATION-PROMPT.md)
and access to this repository. That prompt tells the agent to copy and complete
these files from `docs/templates/` into `docs/`:

1. `DOMAIN-BRIEF.md`
2. `PRODUCT-DECISIONS.md`
3. `SYSTEM-BOUNDARIES.md`
4. `DATA-AND-AUDIT-MODEL.md`
5. `TECHNOLOGY-DECISIONS.md`
6. `MVP-ACCEPTANCE.md`

Complete every `TODO(required)` marker. Keep an explicit `Open questions` section
for non-blocking uncertainty. If a required topic does not apply, write
`Not applicable` and a one-sentence reason.

`IMPLEMENTATION-PLAN.md` is created by the implementation agent after it reviews
the six human-approved inputs. `COMPLETION-REPORT.md` is created at delivery.

## 3. Write decisions, not aspirations

Good project documents use short, testable statements:

- `The first user is an independent clinic manager.`
- `A claim is uniquely identified by the provider reference and service date.`
- `The MVP stops before submitting money movement to a real bank.`

Avoid statements such as `make it scalable`, `use best practices`, or `support
everything`. Quantify success where possible. Separate verified facts, chosen
policy, assumptions, and open questions.

For each external interface, name its owner, exact revision when known, inputs,
outputs, authentication boundary, error behavior, idempotency, and a smallest real
viability check. For each state transition, name the actor, preconditions,
invariants, audit evidence, failure recovery, and rollback boundary.

## 4. Review readiness

Before asking for code:

- confirm the documents do not contradict one another
- confirm the MVP closes one end-to-end user outcome
- remove optional features from the critical path
- identify security, privacy, money, authorization, and destructive-data blockers
- verify legacy code is either explicitly scoped or explicitly excluded
- verify external accounts and credentials are not assumed
- commit the completed decisions as a documentation-only review checkpoint

## 5. Start implementation

Send the agent the text in
[`../prompts/FIRST-IMPLEMENTATION-PROMPT.md`](../prompts/FIRST-IMPLEMENTATION-PROMPT.md).
It is intentionally domain-neutral and reads the product decisions from the
repository. The prompt requires a reviewable atom plan before the first code and
requires exact completion evidence after the final push.
