#!/usr/bin/env bash
# Run the synthetic ERP fixture in a fresh PostgreSQL container.
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "$0")/.." && pwd)
image=${HTMP_AGENT_TEST_POSTGRES_IMAGE:-postgres:15-alpine}
fixture=$(python3 -B "$repo_root/tests/erp_agent_postgres_fixture.py")

{
    cat <<'CONTAINER'
set -eu
pg_dir=$(mktemp -d /tmp/erp-agent-pg.XXXXXX)
initdb -D "$pg_dir" -A trust >/dev/null
pg_ctl -D "$pg_dir" -o "-k $pg_dir -c listen_addresses=''" -l "$pg_dir/server.log" -w start >/dev/null
trap 'pg_ctl -D "$pg_dir" -m fast -w stop >/dev/null' EXIT
psql -X -h "$pg_dir" -U postgres -d postgres -v ON_ERROR_STOP=1 <<'FIXTURE_SQL'
CONTAINER
    printf '%s\n' "$fixture"
    printf '%s\n' FIXTURE_SQL
} | docker run --rm -i --pull never --network none --memory 256m --cpus 1 \
    --user postgres --entrypoint sh "$image" -s
