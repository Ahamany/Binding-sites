#!/usr/bin/env bash
# Warm up data/pdb_cache/ перед оффлайн-демо.
# Скачивает заданный набор PDB с RCSB и кладёт их в кеш.
# Если PDB уже закешировано — пропускает.
#
# Запуск:
#   ./scripts/precache_demo.sh
#   ./scripts/precache_demo.sh 1FBL 1ATP 2RH1   # custom subset

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CACHE_DIR="${PROJECT_ROOT}/data/pdb_cache"
mkdir -p "${CACHE_DIR}"

# Демо-набор по умолчанию = слайды Pre-defense №3 + apo/holo + резерв.
PDBS=("$@")
if [ ${#PDBS[@]} -eq 0 ]; then
    PDBS=(1FBL 1ATP 1HSG 1AKE 1YES 1YET)
fi

OK=0
SKIP=0
FAIL=0

for pdb in "${PDBS[@]}"; do
    upper="$(echo "$pdb" | tr '[:lower:]' '[:upper:]')"
    dest="${CACHE_DIR}/${upper}.pdb"
    if [ -s "$dest" ]; then
        echo "  SKIP  $upper (already cached, $(wc -c < "$dest") bytes)"
        SKIP=$((SKIP+1))
        continue
    fi
    url="https://files.rcsb.org/download/${upper}.pdb"
    if curl -fsS --max-time 30 -o "$dest" "$url"; then
        echo "  OK    $upper ($(wc -c < "$dest") bytes)"
        OK=$((OK+1))
    else
        rm -f "$dest"
        echo "  FAIL  $upper (RCSB fetch failed)"
        FAIL=$((FAIL+1))
    fi
done

echo
echo "=== precache: ${OK} fetched, ${SKIP} skipped, ${FAIL} failed ==="
echo "Cache: ${CACHE_DIR}"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
