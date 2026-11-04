#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
IMAGE="${IMAGE:-mikrotik-zapret2:diagnostic}"
DEST="${DEST:-out/mikrotik-zapret2-diagnostic.tar}"
mkdir -p "$(dirname "$DEST")"
docker image inspect "$IMAGE" >/dev/null
docker save -o "$DEST" "$IMAGE"
sha256sum "$DEST" > "$DEST.sha256"
echo "=== archive ==="
ls -lh "$DEST"
echo "=== checksum ==="
cat "$DEST.sha256"
echo "=== image ==="
docker image inspect "$IMAGE" --format '{{.Id}} {{.Architecture}}/{{.Os}}'
echo "=== archive files ==="
tar tf "$DEST" | head -25
