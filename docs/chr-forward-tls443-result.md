# CHR forwarded HTTPS/TLS 443 through native nfqws2 — PASS

2026-11-05, CHR RouterOS 7.24.6 long-term, container veth 172.29.250.2/30, RouterOS 172.29.250.1/30. Gateway 192.168.11.1 via vlan11. RouterOS policy table `zapret_lab` routes `1.1.1.1/32` via 172.29.250.2; output mangle marks TCP/443 originating from 192.168.11.220. Container has Linux ip_forward=1, nft forward queue number 49162, native nfqws2 without Lua desync.

Operator-observed:
- `/tool fetch url="https://1.1.1.1/cdn-cgi/trace" src-address=192.168.11.220 check-certificate=no output=user` returned HTTP 200.
- Response reported TLSv1.2 and HTTP/1.1; `sni=plaintext`.
- `nft -a list chain ip zapret2_forward_tls443 forward` counted **11 packets, 961 bytes** queued to 49162.
- `grep -c 'packet: id=.* len='` => **11**; `grep -c 'pass unmodified'` => **11**.
- nfqws2 log recognized `TLS client hello is FULL`; also saw TCP SYN/ACK, application data, FIN.
- Only outgoing direction to 1.1.1.1:443 was NFQUEUED. Incoming TLS ServerHello was not queued; the successful HTTPS transaction establishes end-to-end TLS data exchange but not two-direction NFQUEUE interception.

Result: routed HTTPS/TLS through the container's native nfqws2 NFQUEUE works. No DPI-evasion strategy tested and no production security claim. `check-certificate=no` was used for this isolated lab fetch; normal production clients should validate certificates.
