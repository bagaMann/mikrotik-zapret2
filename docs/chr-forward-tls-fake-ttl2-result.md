# CHR TLS fake+badsum with TTL=2 — successful HTTPS

2026-11-06 operator test. CHR 192.168.11.220, container 172.29.250.2, 1.1.1.1 TCP/443, nfqws2 pinned upstream 4080df37c4d1ab70acb527a63a575954e72974e3. RouterOS policy table zapret_lab unchanged.

Baseline unrestricted `fake:blob=fake_default_tls:badsum` failed RouterOS Fetch with `SSL: internal error (6)`. Earlier multi-interface RouterOS PCAP showed 680-byte fake sharing TCP sequence 1 with 152-byte true ClientHello, followed by server-direction ACK 681 and client retransmissions.

New test `fake:blob=fake_default_tls:badsum:ip_ttl=2`:
- `/health` HTTP 200, nfqws2_running true, ip_forward 1.
- HTTPS fetch `https://1.1.1.1/cdn-cgi/trace`: HTTP 200; response reports TLSv1.2.
- `nft forward` counter: 11 packets 961 bytes, queue 49165.
- nfqws2 logs one `TLS client hello is FULL`, one `fake:`, one `rawsend_dissect repeats=1 size=732 badsum=1 ifout=veth-zapret fwmark=40000000`. Original packet `pass unmodified`.
- No repeated client hello observed in log for this transaction.

Interpretation: TTL2 limitation prevents the previously observed TLS failure, consistent with unrestricted fake reaching a downstream stage that affects the TCP stream. This does **not** prove which hop fixes the deliberately bad TCP checksum, nor prove DPI circumvention. Further controlled TTL3 experiment planned.
