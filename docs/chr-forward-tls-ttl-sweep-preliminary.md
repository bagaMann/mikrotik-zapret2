# CHR dynamic TTL sweep — preliminary results

Observed on 2026-11-06. CHR RouterOS 7.24.6, target 1.1.1.1:443, Linux container 172.29.250.2/30, native nfqws2 with upstream fake TLS `badsum`, TTL set by control endpoint.

- Controller initial TTL3: HTTP /health 200, nfqws2_running true, queue 49167.
- TTL4: POST /ttl HTTP 200, subsequent HTTPS `https://1.1.1.1/cdn-cgi/trace` HTTP 200, then /stats reports `clienthello=1` and `fake_invocations=1`.
- TTL5, TTL6, TTL7: POST /ttl HTTP 200, but **no HTTPS request was performed** between these changes; do not count them as success or failure.
- TTL8: POST /ttl HTTP 200, subsequent HTTPS HTTP 200, and /ttl at same TTL reported `clienthello=1`, `fake_invocations=1`.
- TTL9, TTL10, TTL32, TTL64: the controller returned HTTP 400 because the program originally validated TTL range `2..8`; these are not nfqws2 or HTTPS failures.
- Missing POST body also returned HTTP 400 (expected).

Follow-up fix: raise controller validation from 2..8 to 2..64 (commit 1fe7a0735551c2e18fc0e66740abd07e152f01d4). Rebuild/redeploy required; updating GitHub does not change an already running RouterOS container. Suggested follow-up experiments: TTL9, TTL16, TTL32, TTL64, one HTTPS request and /stats after each, stop on first failure and retest nearby values. Repeat tests before claiming a precise boundary.

This experiment checks stability of the HTTPS flow, **not** effectiveness against any particular DPI middlebox.
