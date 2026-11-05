# CHR routed TLS Lua PASS test — SUCCESS

2026-11-05, MikroTik CHR 7.24.6 long-term, host 192.168.11.220, gateway 192.168.11.1, container VETH 172.29.250.2/30. RouterOS output mangle marks TCP/443 to 1.1.1.1 into the zapret_lab table via container; Linux nft forward NFQUEUE 49163 to native nfqws2 with `probe_tls_pass.lua`.

Operator-observed:
- `/health` HTTP 200, `ip_forward=1`, `nfqws2_running=true`.
- `https://1.1.1.1/cdn-cgi/trace` HTTP 200, TLSv1.2, HTTP/1.1.
- `nft -a list chain ip zapret2_forward_tls_lua forward`: `counter packets 12 bytes 1013 queue to 49163`.
- `grep ZAPRET2_FORWARDED_TLS_LUA_PASS` logged three invocations, payload_len=152, 93, 136.
- `grep -c 'pass unmodified'`: 12.

This verifies Lua execution on live routed TLS data and successful end-to-end HTTPS without packet changes. Fake/split DPI desync, injected packet delivery, and production use remain unproven.
