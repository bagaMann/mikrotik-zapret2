# CHR TLS fake+badsum TTL=3 — successful HTTPS

Operator-observed on 2026-11-06, same MikroTik CHR lab 192.168.11.220 and Linux container at 172.29.250.2 as prior TTL2 and unrestricted tests. Native nfqws2 with pinned upstream version.

- `/health` HTTP 200, `ip_forward=1`, `nfqws2_running=true`.
- `https://1.1.1.1/cdn-cgi/trace` returned HTTP 200, TLSv1.2.
- Linux nft forward: `counter packets 11 bytes 961 queue to 49166`.
- One full TLS ClientHello in logs; one `LUA: fake:`; one `rawsend_dissect repeats=1 size=732 badsum=1 ifout=veth-zapret fwmark=40000000`.
- Original ClientHello returned `pass unmodified`; no ClientHello retransmit observed in the test.

Control results: TTL2 also worked; unrestricted fake+badsum caused `SSL: internal error (6)` with remote direction ACK 681 on 680-byte fake despite real TLS ClientHello 152 bytes. Upstream checksum handling or a middlebox remains **unproven**, and TTL3 passing does not establish effective DPI bypass.

Next test container `forward-tls-ttl-sweep`: supports lab-only POST /ttl body `ttl=N`, 2<=N<=8; removes nft queue rules, stops nfqws2, restarts with new TTL, then restores queue for 1.1.1.1 TCP/443. Queue 49167 and control port 49339, initial TTL 3. This avoids repeated images while mapping TTL boundary.
