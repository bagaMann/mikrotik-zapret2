#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
BASE_IMAGE="${BASE_IMAGE:-mikrotik-zapret2:nfqueue-probe}"
IMAGE="${IMAGE:-mikrotik-zapret2:forward-quic-pass}"
docker image inspect "$BASE_IMAGE" >/dev/null
python3 -m py_compile container/probe_forward_quic_pass.py
docker build --platform linux/amd64 --pull=false -f Dockerfile.forward-quic-pass \
  --build-arg "BASE_IMAGE=$BASE_IMAGE" -t "$IMAGE" .
IMAGE="$IMAGE" DEST=out/mikrotik-zapret2-forward-quic-pass.tar \
  bash scripts/export-routeros-docker-archive.sh
