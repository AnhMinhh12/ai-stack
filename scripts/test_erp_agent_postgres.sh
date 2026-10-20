#!/usr/bin/env bash
# Isolated synthetic fixture only: no mounts, network, or production credentials.
set -euo pipefail
AGENT_REPO_ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
AGENT_TEST_TMP=$(mktemp -d /tmp/erp-agent-test.XXXXXX)
trap 'rm -rf -- "$AGENT_TEST_TMP"' EXIT
AGENT_PG_IMAGE=${HTMP_AGENT_TEST_POSTGRES_IMAGE:-postgres@sha256:fe0737ba566a2c5b2a28f34433c0a423261900ec17b9bf7ad115e1aae7e57f1b}
python3 "$AGENT_REPO_ROOT/tests/erp_agent_postgres_fixture.py" > "$AGENT_TEST_TMP/fixture.sql"
cat > "$AGENT_TEST_TMP/run.sh" <<'CONTAINER'
set -eu
AGENT_PG_DATA=$(mktemp -d /tmp/erp-agent-pg.XXXXXX)
initdb -D "$AGENT_PG_DATA" -A trust > /tmp/erp-agent-init.log
pg_ctl -D "$AGENT_PG_DATA" -o '-k /tmp -p 55432 -c listen_addresses=' -l /tmp/erp-agent-pg.log start > /dev/null
trap 'pg_ctl -D "$AGENT_PG_DATA" -m immediate stop >/dev/null' EXIT
psql -h /tmp -p 55432 -U postgres -d postgres -v ON_ERROR_STOP=1 <<'FIXTURE_SQL'
CONTAINER
cat "$AGENT_TEST_TMP/fixture.sql" >> "$AGENT_TEST_TMP/run.sh"
printf '\nFIXTURE_SQL\n' >> "$AGENT_TEST_TMP/run.sh"
docker run --rm -i --network none --memory 256m --cpus 1 --user postgres \
  --entrypoint sh "$AGENT_PG_IMAGE" -s < "$AGENT_TEST_TMP/run.sh"
