# CHR routed QUIC UDP/443 PASS baseline — 2026-11-06

MikroTik CHR RouterOS 7.24.6, Debian test client 192.168.11.18, CHR 192.168.11.220, container 172.29.250.2/30 with Linux ip_forward=1. Traffic to 1.1.1.1/32 routed from Debian via CHR, RouterOS prerouting mangle marks UDP/443 into existing zapret_lab table via VETH. Container runs native nfqws2 NFQUEUE 49168, nft forward rule UDP dport 443 to 1.1.1.1. No active Lua desync.

Evidence supplied by operator:
- Direct Debian curl --http3-only to https://one.one.one.one/cdn-cgi/trace => HTTP/3 200, TLSv1.3, certificate verification OK.
- Same curl through CHR route => HTTP/3 200, TLSv1.3, certificate verification OK.
- nft counter 13 packets 5696 bytes queued to 49168.
- Log reports 'packet contains quic_initial payload'; 'QUIC initial contains CRYPTO with full fragment coverage'; 'l7proto=quic' hostname='one.one.one.one'.
- Log includes REPLAY of initial QUIC packets and one 'packet: id=2 drop' in reassembly path. Eleven 'pass unmodified' lines. Hence not every original queue item is literally PASS; success of HTTP/3 indicates the end-to-end session works, but per-packet behavior requires deeper investigation.
- Test mangle rule removed and Debian /32 route deleted after test.

One SSH SCP operation warned key path /root/.ssh/chr_zapret_ed25519 missing while copying image successfully using alternative SSH authentication; future instructions should avoid assuming this key exists.

No active QUIC DPI evasion tested. This baseline only proves routed HTTP/3 with nfqws2's passive QUIC parsing.
