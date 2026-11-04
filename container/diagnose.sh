#!/bin/sh
set -u
printf '%s\n' '=== mikrotik-zapret2 diagnostic container (NO packet modification) ==='
printf '%s\n' '=== identity ==='
id
printf '%s\n' '=== kernel ==='
uname -a
printf '%s\n' '=== binary ==='
ls -l /usr/local/bin/nfqws2
printf '%s\n' '=== shared libraries ==='
ldd /usr/local/bin/nfqws2 || true
printf '%s\n' '=== interfaces ==='
ip -brief address || true
printf '%s\n' '=== routing ==='
ip route || true
printf '%s\n' '=== netfilter tools ==='
iptables -V || true
nft --version || true
printf '%s\n' '=== available nfqueue modules ==='
if [ -r /proc/net/ip_tables_names ]; then cat /proc/net/ip_tables_names; fi
printf '%s\n' '=== capabilities ==='
grep -E 'Cap(Inh|Prm|Eff|Bnd|Amb):' /proc/self/status || true
printf '%s\n' '=== diagnostic complete; no firewall rules added ==='
