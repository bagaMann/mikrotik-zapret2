#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
BASE_IMAGE="${BASE_IMAGE:-mikrotik-zapret2:nfqueue-probe}"
IMAGE="${IMAGE:-mikrotik-zapret2:nfqws2-lua-drop}"
docker image inspect "$BASE_IMAGE" >/dev/null
python3 -m py_compile container/probe_nfqws2_lua_drop.py
docker build --platform linux/amd64 --pull=false -f Dockerfile.nfqws2-lua-drop \
  --build-arg "BASE_IMAGE=$BASE_IMAGE" -t "$IMAGE" .
IMAGE="$IMAGE" DEST=out/mikrotik-zapret2-nfqws2-lua-drop.tar \
  bash scripts/export-routeros-docker-archive.sh
