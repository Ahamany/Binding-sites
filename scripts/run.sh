#!/usr/bin/env bash
# Запустить FastAPI dev-сервер в conda env annc.

set -euo pipefail

if [[ -z "${CONDA_ENV:-}" ]]; then
    CONDA_BASE="$(conda info --base 2>/dev/null || true)"
    if [[ -z "$CONDA_BASE" ]]; then
        echo "ERROR: conda not found in PATH. Активируйте conda или задайте CONDA_ENV вручную." >&2
        exit 1
    fi
    CONDA_ENV="$CONDA_BASE/envs/annc"
fi
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
P2RANK_DIR="$PROJECT_ROOT/third_party/p2rank"

if [[ ! -x "$CONDA_ENV/bin/uvicorn" ]]; then
    echo "ERROR: uvicorn not found in $CONDA_ENV. Run: pip install -r backend/requirements.txt" >&2
    exit 1
fi

if [[ ! -x "$CONDA_ENV/bin/fpocket" ]]; then
    echo "ERROR: fpocket not in conda env. Run: conda install -n annc -c conda-forge -c bioconda fpocket -y" >&2
    exit 1
fi

if [[ ! -x "$P2RANK_DIR/prank" ]]; then
    echo "WARN: P2Rank not installed at $P2RANK_DIR. Run: ./scripts/install_p2rank.sh" >&2
fi

# Дать обёрткам найти prank/fpocket по PATH
export PATH="$P2RANK_DIR:$CONDA_ENV/bin:$PATH"
export JAVA_HOME="$CONDA_ENV"

cd "$PROJECT_ROOT/backend"
exec "$CONDA_ENV/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --reload
