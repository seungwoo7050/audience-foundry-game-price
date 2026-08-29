# Completion report

## Delivered outcome

- User-visible closed loop: An explicitly approved Steam mapping for Cyberpunk
  2077 Standard Edition (`1091500`, `KR`, `KRW`) can be ingested synchronously by
  Django, validated and committed with receipt/audit evidence in PostgreSQL,
  returned through the read-only `/api/v1` contract, and rendered by Astro with
  current price, source, edition, observation time, and “추적 시작 이후 관찰된
  최저가” wording. An exact replay is a no-op duplicate.
- Explicit non-goals preserved: No competitor data/history, additional store,
  automatic matching, user account, wishlist, alert, payment, affiliate,
  advertisement, scheduler, queue, analytics, production deployment, or direct
  Astro/database write path was introduced.
- Validated and pushed implementation revision: local and `origin/main` were both
  `c208d44800920b10991e2e4dfcd6506f000cdabc` on branch `main` at
  `https://github.com/seungwoo7050/audience-foundry-game-price.git` before this
  report-only closure commit. A Git commit cannot contain its own SHA; the exact
  closure SHA is verified after this report is committed and is stated in the
  final handoff together with the matching remote SHA.
- Clean/dirty state: Clean before the corrected full gate, before the live run,
  and before report creation. Generated Astro output, virtual environments, npm
  modules, and temporary evidence are ignored or outside the repository.

## Evidence

- Focused checks: 7 PostgreSQL schema/Admin tests; 6 deterministic adapter tests;
  10 PostgreSQL ingestion tests; and 3 API contract tests. The ingestion suite
  covers authority denial before fetch, exact-key replay without fetch, duplicate
  receipt, duplicate state, out-of-order history, observed-low update, retryable
  network failure, unexpected fetch redaction, injected transaction rollback,
  pre-tracking rejection, and concurrent same-key submission.
- Full repository gate: `make gate` passed on pushed commit
  `c208d44800920b10991e2e4dfcd6506f000cdabc`. It performed frozen uv/npm installs;
  PostgreSQL 17 tmpfs recreation; Django checks; no-missing-migration check; empty
  migration apply; all 26 backend tests; fixture seed, acceptance, and replay;
  real local API fetch; Astro check and two-page production build; 8 dynamic
  required and 3 forbidden HTML assertions; npm and Python advisory checks;
  lockfile/license/secret checks; and final clean-tree verification.
- Positive deterministic simulation: Fixed game ID
  `11111111-1111-4111-8111-111111111111`, mapping ID
  `22222222-2222-4222-8222-222222222222`, approval identity
  `e0862af9fc674627c0fc109fdc24c6702e517ace01e65214ffa6f09d17014e17`,
  run `050bdcd0-0980-45bc-bdca-be23a03fdbb5`, receipt
  `f8e703d6-1bf9-497c-a24e-8ac3a2f057f7`, and observation
  `dd121491-d4dd-458d-9975-89df39a60880`. The first command returned `ACCEPTED`;
  the exact replay returned `DUPLICATE` with the same identities. The minimized
  fixture SHA-256 is `e7ddabfa49e020f1cdf2c90cbe25bfeb2698d959fc8e5effdf9391bf241deffe`.
- API and Astro simulation: Checked-in v1 contract fixture SHA-256 is
  `1c949c2692c1d433bae2d6f440528cda5963b5838b49a403a83e86d4566c00b8`.
  Astro fetched the real loopback API at build time; the generated game page
  matched title, edition, source, `KRW / KR`, current amount, observed-low amount,
  scope label, and disclaimer, and excluded the three internal/sensitive markers.
- Corrected real interface evidence: The approved adapter revision
  `steam-appdetails-v2-krw-scale` made one corrective read-only HTTPS GET for App
  ID `1091500` at `2026-08-29T13:05:50.348184+00:00`. HTTP status was `200`;
  response SHA-256 was
  `3f5a7e661994f0596c70f40ee9a1da35f75d5b77787e66d0b8abba759f09b19c`;
  receipt identity was
  `e91fc3a4bf05482c366c477bfdb4f5fd830192381a348f9b9bdcb34871fc5cc1`.
  Normalized accepted fields were `KRW`, current `66000`, regular `66000`, and
  discount `0`; raw response content was not retained. Run
  `35395084-5a03-4739-9a89-4ce23a9a8912`, receipt
  `8e7d5cf4-a85a-49d4-a835-ffdfd6c863fc`, and observation
  `29a51b08-4fff-4906-9326-cba3d0280c61` ended `SUCCEEDED`/`ACCEPTED`. Exact-key
  replay returned `DUPLICATE` with the same IDs before adapter invocation, so it
  issued no second request. The resulting API current amount was `66000`, observed
  low remained the simulated `33000`, and all 8 dynamic Astro assertions passed.
- Compatibility failure and correction: The first viability GET at
  `2026-08-29T13:02:19.979579+00:00` disproved the v1 assumption that Steam KRW
  integers were already ISO minor units: a displayed KRW 66,000 price arrived as
  `6600000`. That result existed only in the disposable tmpfs database. Dependent
  acceptance stopped, adapter v2 added exact `/100` normalization plus rejection
  of non-divisible source amounts, 26 tests passed, and the full gate recreated an
  empty database before the corrected proof. This report does not count the v1
  result as valid product evidence.
- Evidence labels: Backend fixtures, operator identities in tests, passwords in
  tests, and the `33000` observed low are deterministic simulations. The corrected
  HTTP receipt/hash and `66000` current price are live read-only evidence. The
  saved HTML comparison is automated local acceptance, not human visual approval
  or production evidence.

## Safety and compatibility

- Security/privacy/authorization: Public routes are GET-only and return only an
  approved published projection. Anonymous mutation receives `405`; unapproved or
  paused mappings fail before network access or canonical writes. Admin requires
  Django staff authentication. No public-user personal data is collected.
- Secret handling: Adapter and ingestion tests inject the recognizable fake value
  `FAKE_SECRET_SHOULD_NOT_ESCAPE` and prove exception details do not enter failure
  state. API, logs, generated HTML, and tracked-file scans excluded secret/internal
  markers. No Steam login, cookie, key, account, payment, or 2FA was used.
- Dependency/license/advisory result: Direct versions and licenses are recorded in
  `THIRD_PARTY_NOTICES.md`. Psycopg 3.3.4 LGPL-3.0-only use was explicitly approved
  for unmodified dynamic server-side use. Frozen npm audit reported 0
  vulnerabilities and pip-audit reported no known vulnerabilities at gate time;
  this does not claim the graph is risk-free.
- Data migration/backward compatibility: `prices.0001_initial` applied to an empty
  PostgreSQL 17 database. `makemigrations --check --dry-run` reported no changes.
  The read-only reverse plan listed explicit undo operations for every model,
  field, and constraint; it was inspected but not applied so live evidence remained
  available. No legacy or destructive data migration occurred. `/api/v1` exactly
  matches its checked-in fixture.
- External state changed and recovery: Steam received two read-only viability GETs:
  the first exposed the scale incompatibility and the second proved adapter v2.
  Replays did not issue GETs. No remote Steam state changed, so no remote rollback
  exists or is needed. Git received normal non-force pushes. Local Docker state is
  one scoped tmpfs PostgreSQL container and generated Astro output; `make db-down`
  deletes the database, and `make gate` recreates both canonical fixture state and
  the site from committed inputs. Live state is intentionally not reproducible
  without another separately authorized read.

## Remaining work

- Human/account checkpoints: Repository/toolchain, Psycopg license, Steam source,
  and exact mapping approvals were completed. A human has not visually compared
  the final generated page with the approved Steam product/edition and recorded
  acceptance. No real Admin password was created or entered. Production branding,
  terms/legal review for ongoing collection, deployment, secrets, backup/restore,
  monitoring, and any scheduled collection remain later checkpoints.
- Blockers and claims not proved: The implementation and automated local/live MVP
  loop are complete. Manual visual acceptance is still unproved. No provider
  sandbox exists; no production, performance, traffic, legal-clearance, retention,
  restore, or continuous-availability claim is made.
- Known risks and deferred scope: The Steam endpoint is unversioned and not treated
  as a stable business contract. Its amount scale and response shape may change;
  adapter rejection will preserve prior published state but requires a new
  viability review. The local password and development server are loopback-only
  conveniences, never production configuration. The observed low includes the
  clearly labeled synthetic fixture value, so it is acceptance evidence rather
  than a production market claim.
