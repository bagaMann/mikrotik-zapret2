# CHR fake+badsum TCP sequence failure — PCAP analysis

Date 2026-11-05. RouterOS 7.24.6 CHR 192.168.11.220 -> 1.1.1.1:443 using policy-routed container 172.29.250.2 and upstream gateway 192.168.11.1. Native nfqws2 uses pinned upstream Lua fake with badsum.

User-provided packet capture `zapret-fake.pcap` (RouterOS multi-interface sniff) and tcpdump decode:

- TCP session source port 47707. TCP 3-way handshake succeeds.
- Real ClientHello TCP payload 152 bytes, relative seq 1:153, 204-byte IP packet, checksum corrected on routed copies (`0x8540 correct`).
- Fake TLS TCP payload 680 bytes, relative seq 1:681, 732-byte IP packet; capture records checksum `0xf517 (incorrect -> 0x2241)` when leaving CHR.
- Remote direction ACK **681** and returns TLS data (`seq 1:2223`) while client retransmits the 152-byte original ClientHello seq 1:153.
- Repeated attempts preserve same relative TCP seq. HTTPS `/tool fetch` fails `SSL: internal error (6)`.
- `nft` previously counted 8 fake packets each 732 bytes in Linux OUTPUT and POSTROUTING. RouterOS raw counter saw both original and fake packets.
- CHR firewall filter empty; only NAT rule was `masquerade src-address=172.29.250.2 out-interface=vlan11` (not matching transit source 192.168.11.220). External upstream gateway 192.168.11.1 handles Internet access.
- Capture contains repeated packet copies across interfaces; these are not distinct network sends.

**Interpretation:** Server-side ACK 681 is consistent with the fake payload entering the remote TCP stream despite the CHR capture showing an incorrect checksum. The most plausible unverified mechanism is checksum normalization at an upstream NAT gateway; a middlebox-generated ACK is another possibility. Confirmation requires capture on both sides of that upstream gateway. Do not claim exact correction point from CHR capture alone.

**Next isolated experiment:** keep fake+badsum but cap injected fake IPv4 TTL at 2, leaving original packets unaltered. If HTTPS recovers this supports the conclusion that an upstream hop or network segment accepts the fake. TTL2 is diagnostic, not a production DPI bypass strategy.
