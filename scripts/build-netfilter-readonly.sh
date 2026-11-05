#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
BASE_IMAGE="${BASE_IMAGE:-mikrotik-zapret2:diagnostic}"
IMAGE="${IMAGE:-mikrotik-zapret2:netfilter-readonly}"
docker image inspect "$BASE_IMAGE" >/dev/null
docker build --platform linux/amd64 --pull=false -f Dockerfile.netfilter-readonly \
  --build-arg "BASE_IMAGE=$BASE_IMAGE" -t "$IMAGE" .
IMAGE="$IMAGE" DEST=out/mikrotik-zapret2-netfilter-readonly.tar \
  bash scripts/export-routeros-docker-archive.sh
