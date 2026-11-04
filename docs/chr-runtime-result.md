# CHR runtime diagnostics — 2026-11-04

User confirmed `mikrotik-zapret2-routeros` starts on RouterOS 7.24.6 and exits with status 0.

- Kernel: `Linux CHR 5.6.3-64`, x86_64.
- Entrypoint: `/usr/local/bin/diagnose`.
- Executable: `/usr/local/bin/nfqws2`, 228024 bytes.
- `ldd`: all required libraries resolved (LuaJIT, zlib, libnetfilter_queue, libnfnetlink, libmnl, glibc, libm, libgcc_s).
- Network: `veth-zapret@if14` UP, `172.29.250.2/30`; default route `172.29.250.1`.
- Tools: iptables 1.8.11 (nf_tables), nftables 1.1.3.
- Capability masks: CapPrm/CapEff/CapBnd `0000003fffffffff`, CapInh/CapAmb zero. Despite `privileged=no`, this is an unusually broad capability set. The diagnostic did not change firewall rules.
- Exit: `*** exited with status 0`.

**Limitations:** `ldd` and the presence of iptables/nftables do not establish that the RouterOS kernel exposes NFQUEUE or nftables netfilter hooks. The current diagnostic did not open an NFQUEUE socket, bind a queue, or test packet interception. The next step is a non-routing, controlled NFQUEUE binding probe, followed by isolated traffic only if kernel support is verified. Review capabilities and hardening before production.
