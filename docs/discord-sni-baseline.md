# Discord TLS SNI baseline — 2026-11-06

Debian 192.168.11.18, upstream direct gateway 192.168.11.1.

DNS for discord.com returned multiple 162.159.x IPv4 addresses. All five individually tested IPv4 addresses timed out on direct curl with Discord SNI. For 162.159.136.232:443 tcpdump observed client SYN, received SYN-ACK after ~28ms, local ACK, ClientHello of 1571 bytes. Remote ACK advanced through first 1388 bytes, subsequent 183-byte TCP segment retransmitted repeatedly without final ACK. Local outbound checksum 'incorrect' is consistent with TX checksum offloading and is not evidence of bad wire checksums.

Reducing TLS ClientHello by constraining key group to X25519 (curl --curves X25519, reports 512-byte TLS ClientHello) still led to a timeout.

Controlled single-IP OpenSSL TLS1.3 tests: SNI example.com at 162.159.136.232:443 completed and verified certificate CN=example.com; SNI discord.com did not complete in 12s. This is strong evidence of SNI-dependent interference along the path, but no specific middlebox has been identified.

Next: keep 1.1.1.1 default test, add dynamic single-target IPv4 nft set (POST /target body ip=162.159.136.232) in combined TCP+UDP container, retain independent NFQUEUE 49170/49171. On CHR add only a /32 zapret_lab route via 172.29.250.2@main and prerouting TCP443 mark for Debian 192.168.11.18. On Debian replace /32 route via CHR. Verify no-interception transit and then enable target, test Discord TLS1.3 with SNI fixed and X25519. Retain safe rollback. Avoid a broad 162.159.0.0/16 route because unrelated Cloudflare traffic shares addresses.
