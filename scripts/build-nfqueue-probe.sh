#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
BASE_IMAGE="${BASE_IMAGE:-mikrotik-zapret2:diagnostic}"
IMAGE="${IMAGE:-mikrotik-zapret2:nfqueue-probe}"
docker image inspect "$BASE_IMAGE" >/dev/null
docker build --platform linux/amd64 --pull=false -f Dockerfile.nfqueue-probe \
  --build-arg "BASE_IMAGE=$BASE_IMAGE" -t "$IMAGE" .
echo "Built $IMAGE"
IMAGE="$IMAGE" DEST=out/mikrotik-zapret2-nfqueue-probe.tar \
  bash scripts/export-routeros-docker-archive.sh
