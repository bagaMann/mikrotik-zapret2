#!/bin/sh
# Read-only checks; no rules are installed or removed.
set -u
echo '=== CHR netfilter read-only probe ==='
echo '=== identity/capabilities ==='
id
grep -E '^Cap(Inh|Prm|Eff|Bnd|Amb):' /proc/self/status || true
echo '=== nft list ruleset ==='
nft list ruleset 2>&1
rc=$?
echo "RESULT NFT_LIST_RULESET_EXIT=$rc"
echo '=== iptables -S ==='
iptables -S 2>&1
rc=$?
echo "RESULT IPTABLES_FILTER_EXIT=$rc"
echo '=== iptables -t mangle -S ==='
iptables -t mangle -S 2>&1
rc=$?
echo "RESULT IPTABLES_MANGLE_EXIT=$rc"
echo '=== iptables legacy availability ==='
if command -v iptables-legacy >/dev/null 2>&1; then
    iptables-legacy -S 2>&1
    rc=$?
    echo "RESULT IPTABLES_LEGACY_EXIT=$rc"
else
    echo 'RESULT IPTABLES_LEGACY_UNAVAILABLE'
fi
echo '=== done; no firewall changes ==='
