# Native nfqws2 NFQUEUE packet test — PASS

Date: 2026-11-05, MikroTik CHR RouterOS 7.24.6 long-term x86_64.

Image: `mikrotik-zapret2-nfqws2-packet.tar`; container root dir `zapret-nfqws2-packet-001`. Diagnostic script `container/probe_nfqws2_packet.py`; queue `49155`; scoped nftables output rule matching UDP to `127.0.0.1:49322`. Native nfqws2 executable used without modifications and with CAP_SETUID/CAP_SETGID removed from child bounding capabilities.

Key observed results (full logs supplied by operator):

```
CMD nft add table ip zapret2_nfqws2_probe rc=0
CMD nft add chain ip zapret2_nfqws2_probe out { type filter hook output priority -100; policy accept; } rc=0
CMD nft add rule ip zapret2_nfqws2_probe out ip daddr 127.0.0.1 udp dport 49322 counter queue num 49155 rc=0
RESULT UDP_SEND_RETURNED=26
RESULT UDP_RECEIVED_BYTES=26 FROM=('127.0.0.1', 57077)
RESULT NFQWS2_PACKET_ACCEPTED
counter packets 1 bytes 54 queue to 49155
NFQWS2 packet: id=1 len=54 mark=00000000 ifin=(0) ifout=lo(1)
NFQWS2 IP4: 127.0.0.1 => 127.0.0.1 proto=udp ttl=64 sport=57077 dport=49322
NFQWS2 desync profile 1 (noname) matches
NFQWS2 no lua functions in this profile
NFQWS2 packet: id=1 pass unmodified
CMD nft delete table ip zapret2_nfqws2_probe rc=0
RESULT NFQWS2_FINAL_RC=0
RESULT NATIVE_NFQWS2_PACKET_TEST_SUCCESS
*** exited with status 0
```

Conclusion: native nfqws2 receives a real UDP packet through nftables NFQUEUE, parses and matches a profile, and returns an unmodified PASS verdict; UDP receiver gets the payload. The test cleans up its scoped nftables table and exits 0. No production RouterOS firewall or routing changes were performed.

Not yet demonstrated: Lua desynchronization actions, packet modification or injection, VETH forwarding, connection routing, production safety/performance. The test process remains UID 0 and is lab-only.
