#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
IMAGE="${IMAGE:-mikrotik-zapret2:diagnostic}"
DEST="${DEST:-out/mikrotik-zapret2-routeros.tar}"
mkdir -p "$(dirname "$DEST")"
command -v skopeo >/dev/null || { echo "Install skopeo: apt install skopeo" >&2; exit 2; }
docker image inspect "$IMAGE" >/dev/null
rm -f "$DEST" "$DEST.sha256"
# Convert the Docker daemon image into a legacy Docker archive, not OCI layout.
skopeo copy --format v2s2 "docker-daemon:$IMAGE" "docker-archive:$DEST:$IMAGE"
# RouterOS importer expects Docker manifest.json and config JSON in the archive.
tar tf "$DEST" | grep -x 'manifest.json' >/dev/null
if tar tf "$DEST" | grep -x 'oci-layout' >/dev/null; then
  echo "Unexpected OCI archive; refusing to use for RouterOS" >&2
  exit 3
fi
tar -xOf "$DEST" manifest.json | python3 -m json.tool
sha256sum "$DEST" > "$DEST.sha256"
ls -lh "$DEST"
cat "$DEST.sha256"
