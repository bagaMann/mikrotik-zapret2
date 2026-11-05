# Lua DROP two-packet loopback test — PASS

2026-11-05, MikroTik CHR RouterOS 7.24.6 long-term, native nfqws2 pinned to upstream `4080df37c4d1ab70acb527a63a575954e72974e3`.

Test: container `mikrotik-zapret2-nfqws2-lua-drop2`; rule restricted to UDP 127.0.0.1:49325, NFQUEUE 49158; two packets sent from same source UDP socket.

Observed:

```
RESULT UDP_SEND_FIRST=22
RESULT UDP_SEND_SECOND=22
RESULT UDP_NOT_DELIVERED_AS_EXPECTED
counter packets 2 bytes 100 queue to 49158
RESULT QUEUED_TWO_PACKETS=True
NFQWS2 LUA: ZAPRET2_LUA_DROP_INVOKED
NFQWS2 applying linux postnat conntrack workaround
NFQWS2 packet: id=1 pass modified. len 50 => 50
NFQWS2 LUA: ZAPRET2_LUA_DROP_INVOKED
NFQWS2 packet: id=2 drop
RESULT NFQWS2_FINAL_RC=0
RESULT LUA_FUNCTION_INVOKED=True
RESULT NFQWS2_SECOND_PACKET_DROPPED=True
RESULT FIRST_PACKET_WORKAROUND=True
RESULT NATIVE_NFQWS2_LUA_DROP_TWO_PACKET_TEST_SUCCESS
*** exited with status 0
```

The first-packet behavior is expected from upstream `nfq2/desync.c` `ct_new_postnat_fix()`, which changes the first dropped packet in a connection to an invalid/low-TTL packet to avoid conntrack teardown after postnat hooks. The second packet receives a true `NF_DROP`. Both were not delivered to the local receiver. The temporary nftables table was deleted successfully. This does not demonstrate VETH forwarding or production policy safety.
