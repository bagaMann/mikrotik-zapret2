#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
BASE_IMAGE="${BASE_IMAGE:-mikrotik-zapret2:nfqueue-probe}"
IMAGE="${IMAGE:-mikrotik-zapret2:forward-tls-fake}"
PIN="4080df37c4d1ab70acb527a63a575954e72974e3"
docker image inspect "$BASE_IMAGE" >/dev/null
python3 -m py_compile container/probe_forward_tls_fake.py
mkdir -p out/zapret2-upstream-lua
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
git clone --quiet --filter=blob:none --no-checkout https://github.com/bol-van/zapret2.git "$TMP/zapret2"
git -C "$TMP/zapret2" checkout --quiet --detach "$PIN"
test "$(git -C "$TMP/zapret2" rev-parse HEAD)" = "$PIN"
cp "$TMP/zapret2/lua/zapret-lib.lua" out/zapret2-upstream-lua/
cp "$TMP/zapret2/lua/zapret-antidpi.lua" out/zapret2-upstream-lua/
printf '%s\n' "$PIN" > out/zapret2-upstream-lua/commit.txt
docker build --platform linux/amd64 --pull=false -f Dockerfile.forward-tls-fake \
  --build-arg "BASE_IMAGE=$BASE_IMAGE" -t "$IMAGE" .
IMAGE="$IMAGE" DEST=out/mikrotik-zapret2-forward-tls-fake.tar \
  bash scripts/export-routeros-docker-archive.sh
