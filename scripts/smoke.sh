#!/usr/bin/env bash
# End-to-end smoke test: гоняет 6 сценариев против работающего API.
# Предполагает что uvicorn запущен на http://localhost:${PORT:-8000}.
#
# Запуск:
#   ./scripts/run.sh &      # в одном терминале
#   ./scripts/smoke.sh      # в другом

set -euo pipefail

PORT="${PORT:-8000}"
BASE="http://localhost:${PORT}/api"
DEMO_PDB="${DEMO_PDB:-1FBL}"

PASS=0
FAIL=0
log_ok()   { echo "  PASS  $1"; PASS=$((PASS+1)); }
log_err()  { echo "  FAIL  $1"; FAIL=$((FAIL+1)); }

require() {
    local name="$1"; shift
    local expect="$1"; shift
    local actual
    actual=$("$@")
    if [[ "$actual" == "$expect" ]]; then
        log_ok "$name (got $actual)"
    else
        log_err "$name (expected $expect, got $actual)"
    fi
}

http_code() {
    curl -s -o /dev/null -w '%{http_code}' "$@"
}

poll_status() {
    local job="$1"
    for i in $(seq 1 60); do
        local status
        status=$(curl -sf "$BASE/jobs/$job" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
        if [[ "$status" == "done" || "$status" == "failed" ]]; then
            echo "$status"
            return
        fi
        sleep 2
    done
    echo "timeout"
}

echo "=== 1. health ==="
require "GET /api/health → 200"  "200"  http_code "$BASE/health"

echo "=== 2. happy path: pdb_id=$DEMO_PDB ==="
JOB_ID=$(curl -sf -X POST "$BASE/jobs" -F "pdb_id=$DEMO_PDB" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")
echo "  job_id=$JOB_ID"
STATUS=$(poll_status "$JOB_ID")
[[ "$STATUS" == "done" ]] && log_ok "job done in time" || log_err "job final status=$STATUS"

P_COUNT=$(curl -sf "$BASE/jobs/$JOB_ID" \
    | python3 -c "import sys,json; print(len(json.load(sys.stdin)['results']['p2rank']['pockets']))")
F_COUNT=$(curl -sf "$BASE/jobs/$JOB_ID" \
    | python3 -c "import sys,json; print(len(json.load(sys.stdin)['results']['fpocket']['pockets']))")
[[ "$P_COUNT" -gt 0 ]] && log_ok "P2Rank pockets: $P_COUNT" || log_err "P2Rank empty"
[[ "$F_COUNT" -gt 0 ]] && log_ok "fpocket pockets: $F_COUNT" || log_err "fpocket empty"

echo "=== 3. download CSV ==="
CSV=$(curl -sf "$BASE/jobs/$JOB_ID/results.csv")
LINES=$(echo "$CSV" | wc -l)
[[ "$LINES" -gt 1 ]] && log_ok "CSV has $LINES lines (header+rows)" || log_err "CSV too short"
echo "$CSV" | head -1 | grep -q "^method,rank,score" && log_ok "CSV header correct" || log_err "CSV header wrong"

echo "=== 4. download structure (PDB) ==="
PDB_BYTES=$(curl -sf "$BASE/jobs/$JOB_ID/structure" | wc -c)
[[ "$PDB_BYTES" -gt 1000 ]] && log_ok "structure $PDB_BYTES bytes" || log_err "structure too small"

echo "=== 5. file upload ==="
TMP_PDB=$(mktemp --suffix=.pdb)
curl -sf "$BASE/jobs/$JOB_ID/structure" -o "$TMP_PDB"
UP_JOB=$(curl -sf -X POST "$BASE/jobs" -F "file=@$TMP_PDB" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")
rm -f "$TMP_PDB"
echo "  upload job_id=$UP_JOB"
UP_STATUS=$(poll_status "$UP_JOB")
[[ "$UP_STATUS" == "done" ]] && log_ok "upload-job done" || log_err "upload-job final=$UP_STATUS"

echo "=== 6. validation: bad pdb_id format ==="
require "POST /jobs pdb_id=XYZ → 422"  "422"  http_code -X POST "$BASE/jobs" -F "pdb_id=XYZ"
require "POST /jobs pdb_id= 1FBLZ → 422" "422" http_code -X POST "$BASE/jobs" -F "pdb_id=1FBLZ"
require "POST /jobs no input → 400"     "400"  http_code -X POST "$BASE/jobs"

echo "=== 7. 404 on unknown job_id ==="
require "GET /jobs/nope → 404"             "404"  http_code "$BASE/jobs/nope"
require "GET /jobs/nope/results → 404"     "404"  http_code "$BASE/jobs/nope/results"
require "GET /jobs/nope/results.csv → 404" "404"  http_code "$BASE/jobs/nope/results.csv"
require "GET /jobs/nope/structure → 404"   "404"  http_code "$BASE/jobs/nope/structure"

echo "=== 8. listing ==="
LIST_LEN=$(curl -sf "$BASE/jobs" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
[[ "$LIST_LEN" -ge 2 ]] && log_ok "listing has $LIST_LEN jobs" || log_err "listing too short"

echo "=== 9. failed job: bogus pdb_id 9ZZZ ==="
BAD_JOB=$(curl -sf -X POST "$BASE/jobs" -F "pdb_id=9ZZZ" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")
BAD_STATUS=$(poll_status "$BAD_JOB")
[[ "$BAD_STATUS" == "failed" ]] && log_ok "9ZZZ → failed" || log_err "9ZZZ final=$BAD_STATUS"
BAD_ERR=$(curl -sf "$BASE/jobs/$BAD_JOB" | python3 -c "import sys,json; print(json.load(sys.stdin)['error'])")
echo "  error: $BAD_ERR"
echo "$BAD_ERR" | grep -qi "not found" && log_ok "error message readable" || log_err "error not readable: $BAD_ERR"

echo
echo "================================="
echo " RESULT: $PASS passed, $FAIL failed"
echo "================================="
exit $FAIL
