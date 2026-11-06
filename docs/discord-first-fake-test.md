# Discord first active desync test (2026-11-06)

Operator repeated identical HTTPS request to Discord IP 162.159.136.232 with TLS1.3 SNI discord.com and X25519, first via CHR without NFQUEUE target enabled and then after POST /target (ip=162.159.136.232).

- Control without interception: connection timed out after ~5 seconds.
- After enabling target (HTTP controller returned ok=true), still connection timed out after ~5 seconds (HTTP=000).
- Container nft forward rule TCP UDP 443 matching @targets; TCP NFQUEUE 49170: 13 packets, 5854 bytes. UDP NFQUEUE 49171: 0.
- nfqws2 parsed FULL ClientHello (packet len569) on retransmissions. Lua fake_default_tls:badsum:ip_ttl=8 fired repeatedly, rawsend_dissect size732 badsum=1. Original packet passed unmodified. No TLS success.
- CHR mangle and /32 route, Debian /32 route removed, target reset to 1.1.1.1. HTTPS failure was **not** repaired by this fake strategy. The earlier SNI example.com handshake on the same IP succeeded whereas discord.com did not.
- Next stage: same combined container configurable at runtime with POST /tcp-mode mode=fake|multisplit|multidisorder; use one test IP and identical curl TLS1.3 X25519 request. Changing mode briefly removes the TCP nft NFQUEUE rule and restarts TCP nfqws2, and MUST be done when no marked client test traffic is ongoing. RouterOS routes stay tightly limited to the test IP and client. QUIC strategy unchanged.
