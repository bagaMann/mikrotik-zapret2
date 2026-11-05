# CHR netfilter read-only result — 2026-11-05

User executed the `mikrotik-zapret2-netfilter-readonly` container on RouterOS 7.24.6.

All checks succeeded:

- `nft list ruleset` => `NFT_LIST_RULESET_EXIT=0` (no rules printed)
- `iptables -S` => `IPTABLES_FILTER_EXIT=0`, INPUT/FORWARD/OUTPUT ACCEPT
- `iptables -t mangle -S` => `IPTABLES_MANGLE_EXIT=0`, all built-in chains ACCEPT
- `iptables-legacy -S` => `IPTABLES_LEGACY_EXIT=0`
- Container exited status 0; no firewall changes.

Prior test confirmed queue 49152 can be registered and released with libnetfilter_queue.

**Interpretation:** netfilter control-plane reads and NFQUEUE registration work in the container's Linux network namespace. Neither establishes that nft/iptables can add a queue rule, that packets reach the queue, or that RouterOS forwarding traffic traverses the container. Next step is a bounded, isolated loopback packet interception test with guaranteed rule cleanup; avoid production RouterOS firewall changes.
