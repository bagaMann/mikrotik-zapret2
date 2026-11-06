# CHR active QUIC fake test — HTTP/3 pass

Operator results from 2026-11-06. Debian 192.168.11.18 routed UDP/443 via CHR 192.168.11.220 -> 172.29.250.2/30 -> native nfqws2. Destination 1.1.1.1:443, SNI one.one.one.one. Pinned upstream bol-van/zapret2 4080df37c4d1ab70acb527a63a575954e72974e3.

- Image forward-quic-fake health returned HTTP 200 and nfqws2_running=true.
- curl --http3-only https://one.one.one.one/cdn-cgi/trace returned HTTP/3 200, valid server cert, TLS1.3, with the test route active.
- nft Linux NFQUEUE rule: UDP 1.1.1.1:443 queue 49169: 12 packets, 4468 bytes.
- QUIC Initial was identified and CRYPTO had full fragment coverage.
- Lua profile fake:blob=fake_default_quic:ip_ttl=8, sent two rawsend attempts with size 648 and badsum=0. Log showed id1 pass modified (1228->1228), id2 drop/replay, further packets pass unmodified.
- After test, operator removed the temporary CHR mangle entry and Debian's temporary /32 route.

**Limitations:** successful HTTP/3 demonstrates functional QUIC despite active fake, not successful DPI circumvention. The byte string fake_default_quic is a canned upstream sample; not necessarily an effective real-world DPI strategy. The TTL8 TCP safety threshold cannot be assumed equivalent for UDP.

Next stage: combined image with independent TCP and UDP nfqws2 processes and Linux NFQUEUEs 49170 and 49171, targeting only 1.1.1.1:443, HTTP control endpoint 172.29.250.2:49342. TCP TLS profile fake_default_tls:badsum:ip_ttl=8; UDP QUIC profile fake_default_quic:ip_ttl=8. Test both TCP TLS1.3 and UDP QUIC with route and CHR mangle in place, then roll back. Do not put into production until both are proven in the combined image.
