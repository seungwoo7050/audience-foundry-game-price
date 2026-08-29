# Implementation plan

Create this file only after all required decision documents are complete. Each row
is one reviewable commit atom and answers one primary review question.

| Atom | Review question and purpose | Expected files/dependencies | Focused proof | Rollback boundary | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | TODO(required) | TODO(required) | TODO(required) | TODO(required) | planned |

## Ordering rationale

Explain why schema/fixtures, high-risk viability spikes, core behavior, failure
paths, end-to-end gate, documentation, and final remote verification appear in this
order. Separate dependency/import/generated churn from behavior.

TODO(required)

## Size exceptions

Record any atom expected to exceed the thresholds in `DEVELOPMENT-RULES.md`, or
state that no exception is planned.

TODO(required)

## Blocking findings

Security, authorization, data integrity, destructive migration, secret exposure,
idempotency, audit atomicity, and external-interface incompatibility findings stop
dependent work until resolved or explicitly re-scoped.
