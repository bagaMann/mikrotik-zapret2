#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
test -x out/nfqws2 || { echo 'Missing out/nfqws2; compile it first' >&2; exit 2; }
EXPECTED="$(cut -d' ' -f1 out/nfqws2.sha256)"
ACTUAL="$(sha256sum out/nfqws2 | cut -d' ' -f1)"
[[ "$EXPECTED" == "$ACTUAL" ]] || { echo 'Binary SHA256 mismatch' >&2; exit 3; }
IMAGE="${IMAGE:-mikrotik-zapret2:diagnostic}"
docker build --platform linux/amd64 --pull -t "$IMAGE" .
echo "Built $IMAGE"
docker image inspect "$IMAGE" --format '{{.Id}}'
