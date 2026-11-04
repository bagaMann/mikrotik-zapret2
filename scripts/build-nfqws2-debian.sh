#!/usr/bin/env bash
set -Eeuo pipefail
# Build on a disposable Debian amd64 VM. Does NOT install or run services.
# Usage: ZAPRET2_COMMIT=<full-40-character-commit> bash scripts/build-nfqws2-debian.sh
: "${ZAPRET2_COMMIT:?Set ZAPRET2_COMMIT to an audited full 40-character upstream SHA}"
[[ "${ZAPRET2_COMMIT}" =~ ^[0-9a-fA-F]{40}$ ]] || { echo "Invalid SHA" >&2; exit 2; }
command -v git >/dev/null
command -v make >/dev/null
command -v gcc >/dev/null
command -v sha256sum >/dev/null
OUT="${OUT:-$PWD/out}"
mkdir -p "$OUT"
OUT="$(realpath "$OUT")"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
git clone --no-checkout https://github.com/bol-van/zapret2.git "$WORK/zapret2"
git -C "$WORK/zapret2" checkout --detach "$ZAPRET2_COMMIT"
ACTUAL="$(git -C "$WORK/zapret2" rev-parse HEAD)"
[[ "$ACTUAL" == "$ZAPRET2_COMMIT" ]] || { echo "SHA mismatch" >&2; exit 3; }
make -C "$WORK/zapret2/nfq2"
BIN="$WORK/zapret2/nfq2/nfqws2"
test -x "$BIN"
file "$BIN"
cp "$BIN" "$OUT/nfqws2"
sha256sum "$OUT/nfqws2" > "$OUT/nfqws2.sha256"
printf '%s\n' "$ACTUAL" > "$OUT/upstream-commit.txt"
"$OUT/nfqws2" --help > "$OUT/help.txt" 2>&1 || { echo "Help smoke test failed" >&2; exit 4; }
echo "Built and smoke-tested $OUT/nfqws2 at $ACTUAL"
