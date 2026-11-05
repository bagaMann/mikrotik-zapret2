#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
BASE_IMAGE="${BASE_IMAGE:-mikrotik-zapret2:nfqueue-probe}"
IMAGE="${IMAGE:-mikrotik-zapret2:forward-tls-lua}"
docker image inspect "$BASE_IMAGE" >/dev/null
python3 -m py_compile container/probe_forward_tls_lua.py
docker build --platform linux/amd64 --pull=false -f Dockerfile.forward-tls-lua \
  --build-arg "BASE_IMAGE=$BASE_IMAGE" -t "$IMAGE" .
IMAGE="$IMAGE" DEST=out/mikrotik-zapret2-forward-tls-lua.tar \
  bash scripts/export-routeros-docker-archive.sh
