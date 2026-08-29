#!/usr/bin/env bash
set -euo pipefail

GAMEPRICE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GAMEPRICE_API_LOG="/tmp/gameprice-django-gate.log"
GAMEPRICE_API_JSON="/tmp/gameprice-api-v1.json"
GAMEPRICE_ACCEPTED_JSON="/tmp/gameprice-fixture-accepted.json"
GAMEPRICE_REPLAY_JSON="/tmp/gameprice-fixture-replay.json"
GAMEPRICE_SERVER_PID=""

cleanup_server() {
  if [[ -n "$GAMEPRICE_SERVER_PID" ]]; then
    kill "$GAMEPRICE_SERVER_PID" 2>/dev/null || true
    wait "$GAMEPRICE_SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup_server EXIT

cd "$GAMEPRICE_ROOT"
[[ -z "$(git status --porcelain)" ]] || { echo "gate requires a clean worktree"; exit 1; }
[[ "$(python3 --version)" == "Python 3.12.13" ]]
[[ "$(uv --version | awk '{print $2}')" == "0.7.20" ]]
[[ "$(fnm exec --using=22.22.0 -- node --version)" == "v22.22.0" ]]
[[ "$(fnm exec --using=22.22.0 -- npm --version)" == "11.4.2" ]]

uv sync --directory backend --frozen
fnm exec --using=22.22.0 -- npm --prefix web ci
docker compose -p gameprice-mvp down --volumes --remove-orphans
docker compose -p gameprice-mvp up --detach --wait db

backend/.venv/bin/python backend/manage.py check
backend/.venv/bin/python backend/manage.py makemigrations --check --dry-run
backend/.venv/bin/python backend/manage.py migrate --noinput
backend/.venv/bin/python backend/manage.py test prices --verbosity 1
backend/.venv/bin/python backend/manage.py seed_mvp_catalog \
  --actor human-product-owner --human-approved
backend/.venv/bin/python backend/manage.py ingest_price \
  22222222-2222-4222-8222-222222222222 \
  --idempotency-key fixture-gate-v1 \
  --actor operator-fixture \
  --fixture backend/prices/tests/fixtures/steam_success.json \
  --fetched-at 2026-08-29T02:00:00Z > "$GAMEPRICE_ACCEPTED_JSON"
backend/.venv/bin/python backend/manage.py ingest_price \
  22222222-2222-4222-8222-222222222222 \
  --idempotency-key fixture-gate-v1 \
  --actor operator-fixture \
  --fixture backend/prices/tests/fixtures/steam_success.json \
  --fetched-at 2026-08-29T02:00:00Z > "$GAMEPRICE_REPLAY_JSON"
rg -q '"outcome": "ACCEPTED"' "$GAMEPRICE_ACCEPTED_JSON"
rg -q '"outcome": "DUPLICATE"' "$GAMEPRICE_REPLAY_JSON"

backend/.venv/bin/python backend/manage.py runserver 127.0.0.1:8000 --noreload \
  > "$GAMEPRICE_API_LOG" 2>&1 &
GAMEPRICE_SERVER_PID=$!
for _attempt in {1..40}; do
  if curl --fail --silent --show-error \
    http://127.0.0.1:8000/api/v1/games/cyberpunk-2077/ \
    --output "$GAMEPRICE_API_JSON"; then
    break
  fi
  sleep 0.25
done
[[ -s "$GAMEPRICE_API_JSON" ]]

fnm exec --using=22.22.0 -- npm --prefix web run check
fnm exec --using=22.22.0 -- npm --prefix web run build
GAMEPRICE_EXPECTED_API_JSON="$GAMEPRICE_API_JSON" \
  fnm exec --using=22.22.0 -- npm --prefix web run test:render
fnm exec --using=22.22.0 -- npm --prefix web audit
uv run --directory backend --with pip-audit pip-audit --local

[[ "$(find backend -maxdepth 2 -name 'uv.lock' | wc -l | tr -d ' ')" == "1" ]]
[[ "$(find web -maxdepth 2 -name 'package-lock.json' | wc -l | tr -d ' ')" == "1" ]]
! find backend web \( -name 'poetry.lock' -o -name 'Pipfile.lock' -o -name 'pnpm-lock.yaml' -o -name 'yarn.lock' \) | grep -q .
git grep -I -E 'AKIA[0-9A-Z]{16}|BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY|Bearer [A-Za-z0-9_-]{24,}' && exit 1 || true
! rg -n 'FAKE_SECRET_SHOULD_NOT_ESCAPE' web/dist "$GAMEPRICE_API_JSON" "$GAMEPRICE_API_LOG"
rg -q 'Django.*5\.2\.17' THIRD_PARTY_NOTICES.md
rg -q 'Psycopg.*3\.3\.4' THIRD_PARTY_NOTICES.md
rg -q 'Astro.*7\.2\.9' THIRD_PARTY_NOTICES.md

cleanup_server
GAMEPRICE_SERVER_PID=""
[[ -z "$(git status --porcelain)" ]]
echo "repository gate passed: backend tests, fixture loop, API, Astro, advisories, secrets, clean tree"
