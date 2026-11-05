# Native nfqws2 Lua VERDICT_MODIFY — PASS

Date: 2026-11-05. Lab MikroTik CHR RouterOS 7.24.6 long-term, linux/amd64; native nfqws2 pinned upstream commit `4080df37c4d1ab70acb527a63a575954e72974e3`.

Test image: `mikrotik-zapret2-nfqws2-lua-modify.tar`; isolated loopback UDP `127.0.0.1:49326`; NFQUEUE `49159`, private nftables table `ip zapret2_lua_modify_probe`. Lua file `container/probe_modify.lua` changes `desync.dis.payload` from `zapret2-lua-original` to `zapret2-lua-modified` and returns `VERDICT_MODIFY`. Python receiver explicitly compares received payload to expected transformed bytes.

Observed in operator-provided log:

```
CMD nft add rule ip zapret2_lua_modify_probe out ip daddr 127.0.0.1 udp dport 49326 counter queue num 49159 rc=0
RESULT UDP_SEND_RETURNED=20
RESULT UDP_RECEIVED_BYTES=20 FROM=('127.0.0.1', 41355)
RESULT NFQWS2_PACKET_MODIFIED
counter packets 1 bytes 48 queue to 49159
CMD nft delete table ip zapret2_lua_modify_probe rc=0
NFQWS2 LUA: ZAPRET2_LUA_MODIFY_INVOKED
NFQWS2 reconstructed packet due to VERDICT_MODIFY. size 48 => 48
NFQWS2 packet: id=1 pass modified. len 48 => 48
RESULT NFQWS2_FINAL_RC=0
RESULT LUA_FUNCTION_INVOKED=True
RESULT NFQWS2_MODIFIED_VERDICT=True
RESULT NATIVE_NFQWS2_LUA_MODIFY_TEST_SUCCESS
*** exited with status 0
```

This confirms true Lua-based packet modification through native nfqws2, kernel NFQUEUE, and delivery to an application in the container namespace. All three PASS / DROP / MODIFY have now been validated in the loopback lab. This does not establish VETH/Routing integration, practical DPI desync strategies, performance, or production readiness. Running UID=0 is a laboratory-only arrangement; restrict capabilities before production use.
