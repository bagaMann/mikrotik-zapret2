#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
BASE_IMAGE="${BASE_IMAGE:-mikrotik-zapret2:nfqueue-probe}"
IMAGE="${IMAGE:-mikrotik-zapret2:nfqueue-packet}"
docker image inspect "$BASE_IMAGE" >/dev/null
docker build --platform linux/amd64 --pull=false -f Dockerfile.nfqueue-packet \
  --build-arg "BASE_IMAGE=$BASE_IMAGE" -t "$IMAGE" .
IMAGE="$IMAGE" DEST=out/mikrotik-zapret2-nfqueue-packet.tar \
  bash scripts/export-routeros-docker-archive.sh
