#!/usr/bin/env bash
# Скачать P2Rank в third_party/p2rank/
# Используется при первой установке и в CI.

set -euo pipefail

VERSION="${P2RANK_VERSION:-2.5.1}"
DEST="$(cd "$(dirname "$0")/.." && pwd)/third_party"
URL="https://github.com/rdk/p2rank/releases/download/${VERSION}/p2rank_${VERSION}.tar.gz"

mkdir -p "$DEST"
cd "$DEST"

if [[ -x "p2rank/prank" ]]; then
    echo "P2Rank already installed at $DEST/p2rank"
    exit 0
fi

echo "Downloading P2Rank ${VERSION}…"
curl -sL -o p2rank.tar.gz "$URL"
tar xzf p2rank.tar.gz
rm p2rank.tar.gz
mv "p2rank_${VERSION}" p2rank

echo "Installed to $DEST/p2rank"
"$DEST/p2rank/prank" --help 2>&1 | head -1 || true
