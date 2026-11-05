#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
BASE_IMAGE="${BASE_IMAGE:-mikrotik-zapret2:nfqueue-probe}"
IMAGE="${IMAGE:-mikrotik-zapret2:veth-egress}"
docker image inspect "$BASE_IMAGE" >/dev/null
python3 -m py_compile container/probe_veth_egress.py
docker build --platform linux/amd64 --pull=false -f Dockerfile.veth-egress \
  --build-arg "BASE_IMAGE=$BASE_IMAGE" -t "$IMAGE" .
IMAGE="$IMAGE" DEST=out/mikrotik-zapret2-veth-egress.tar \
  bash scripts/export-routeros-docker-archive.sh
