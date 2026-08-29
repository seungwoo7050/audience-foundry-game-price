# Third-party notices

Direct dependencies are installed only from their named package registries and are
reproduced by committed integrity lockfiles. No dependency source is vendored or
modified in this repository.

| Dependency | Version | Source | License | Intended use and obligations |
| --- | --- | --- | --- | --- |
| Django | 5.2.17 | `https://pypi.org/project/Django/5.2.17/` | BSD-3-Clause | Backend framework. Preserve its copyright and license notice when redistributing Django itself. |
| Psycopg | 3.3.4 | `https://pypi.org/project/psycopg/3.3.4/` | LGPL-3.0-only | Django PostgreSQL adapter. Human-approved on 2026-08-29 for unmodified, dynamically used server-side installation; recipients must retain applicable LGPL rights when Psycopg itself is redistributed. |
| Psycopg Binary | 3.3.4 | `https://pypi.org/project/psycopg-binary/3.3.4/` | LGPL-3.0-only | Platform binary selected by the Psycopg `binary` extra under the same human approval and obligations. |
| Astro | 7.2.9 | `https://www.npmjs.com/package/astro/v/7.2.9` | MIT | Static public-site framework; retain its license notice when redistributing Astro itself. |
| @astrojs/check | 0.9.10 | `https://www.npmjs.com/package/@astrojs/check/v/0.9.10` | MIT | Build-time Astro validation; retain its license notice when redistributed. |
| TypeScript | 6.0.3 | `https://www.npmjs.com/package/typescript/v/6.0.3` | Apache-2.0 | Build-time type checking; preserve the license and notices when redistributed. |

`backend/uv.lock` and `web/package-lock.json` record the exact transitive graph and
package hashes/resolution metadata. Registry advisory checks are evidence for known
published advisories at check time, not a claim that the dependency graph is risk-free.
No competitor source, mapping, dataset, or historical price is included.
