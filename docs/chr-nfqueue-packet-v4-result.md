# CHR NFQUEUE packet test v4 — PASS

Date: 2026-11-05. CHR RouterOS 7.24.6 long-term x86_64.

Test container: `mikrotik-zapret2-nfqueue-packet-v4`; image from `Dockerfile.nfqueue-packet`, with `nfq_set_mode(queue, NFQNL_COPY_PACKET, 65535)`.

Observed logs:

```
CMD nft add table ip zapret2_probe rc 0
CMD nft add chain ip zapret2_probe out { type filter hook output priority -100; policy accept; } rc 0
CMD nft add rule ip zapret2_probe out ip daddr 127.0.0.1 udp dport 49321 counter queue num 49153 rc 0
RESULT NFQ_SET_COPY_PACKET_MODE_RC=0 errno=0
RESULT UDP_SEND_RETURNED bytes=17
RESULT NFQ_FD=3
counter packets 1 bytes 45 queue to 49153
RESULT NFQ_FD_READABLE
RESULT NFQ_NETLINK_BYTES=89
RESULT NFQUEUE_PACKET_RECEIVED id=1
RESULT LOOPBACK_PACKET_ACCEPTED
CMD nft delete table ip zapret2_probe rc 0
RESULT TEST_SUCCESS
*** exited with status 0
```

Conclusion: nftables output hook matched one local UDP packet, NFQUEUE delivered it to userspace via netlink, callback issued ACCEPT verdict, and local UDP receiver got original payload. The temporary table was deleted. Reading `/proc/net/netfilter/nfnetlink_queue` returned EACCES, which did not prevent NFQUEUE processing.

Scope limitation: This does **not** establish that `nfqws2` works or that forwarded RouterOS traffic can traverse VETH/container netfilter. Next test should invoke native `nfqws2` with a narrowly scoped local packet, then independently test VETH routing, with rollback and without altering production firewall.
