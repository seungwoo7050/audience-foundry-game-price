# GamePrice KR

GamePrice KR is a Korean-language PC-game price MVP. It stores approved KRW
observations for an operator-mapped Steam product and shows the current price and
the lowest price observed **since this product began tracking it**. It does not
claim an all-time market low or import competitor history.

The first closed loop is intentionally small: Cyberpunk 2077, Steam App ID
`1091500`, Korean region, and Standard Edition. Django owns approval, ingestion,
PostgreSQL state, audit evidence, and `/api/v1`; Astro is a read-only static
consumer. Production deployment, scheduling, accounts, alerts, affiliate links,
and additional stores are out of scope.

## Approved local runtime

- Python 3.12.13, uv 0.7.20, Django 5.2.17
- Node.js 22.22.0, npm 11.4.2, Astro 7.2.9
- PostgreSQL 17 (`postgres:17.6-bookworm`)

The committed PostgreSQL password is a disposable loopback-only development value.
Production configuration has no defaults: keep database and Django secrets out of
Git and set `DJANGO_DEBUG=0` plus `DJANGO_SECRET_KEY` through managed runtime
configuration. The compose database uses tmpfs and is deleted by `make db-down`.

## Run locally

```sh
uv sync --directory backend --frozen
fnm exec --using=22.22.0 -- npm --prefix web ci
make db-up
backend/.venv/bin/python backend/manage.py migrate
backend/.venv/bin/python backend/manage.py seed_mvp_catalog \
  --actor human-product-owner --human-approved
backend/.venv/bin/python backend/manage.py ingest_price \
  22222222-2222-4222-8222-222222222222 \
  --idempotency-key local-fixture-v1 --actor operator-fixture \
  --fixture prices/tests/fixtures/steam_success.json
backend/.venv/bin/python backend/manage.py runserver 127.0.0.1:8000
```

In another terminal:

```sh
fnm exec --using=22.22.0 -- npm --prefix web run check
fnm exec --using=22.22.0 -- npm --prefix web run build
fnm exec --using=22.22.0 -- npm --prefix web run test:render
```

Open `web/dist/index.html` through any local static file server. The generated site
is disposable; PostgreSQL remains canonical. Stop and delete the disposable
database with `make db-down`.

## Full repository gate

From a clean checkout with Docker running:

```sh
make gate
```

The gate recreates an empty PostgreSQL 17 database, installs from both lockfiles,
checks and applies migrations, runs the complete backend suite, closes and replays
the deterministic fixture loop, builds Astro through the real local API, asserts
the generated HTML, checks published advisories, scans for secret exposure, and
finishes only when the Git worktree is clean.

The approved live Steam request is manual and separate from the deterministic
gate. It performs one read-only request and records only normalized fields,
timestamps, stable identities, and a response SHA-256—not cookies, credentials,
headers, or the raw response body.

The implementation contract and evidence requirements are in [`docs/`](docs/),
starting with [`docs/PRODUCT-DECISIONS.md`](docs/PRODUCT-DECISIONS.md) and
[`docs/MVP-ACCEPTANCE.md`](docs/MVP-ACCEPTANCE.md).
