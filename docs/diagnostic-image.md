# Diagnostic image — stage 2

**Experimental only.** Uses the moving `debian:trixie-slim` base and apt repository versions, so it is NOT yet a reproducible release. The final image must pin the base digest and dependencies after validation. No security audit or RouterOS NFQUEUE compatibility has been completed.

Build on Debian after compiling the pinned upstream binary:

```bash
cd /opt/mikrotik-zapret2
git pull --ff-only
bash scripts/build-diagnostic-image.sh
docker run --rm --network none --cap-drop ALL mikrotik-zapret2:diagnostic
docker image inspect mikrotik-zapret2:diagnostic --format '{{.Id}}'
```

The diagnostic image does **not** invoke `nfqws2`, create firewall rules, or start a background service. It only prints environment, libraries, interfaces, routes and capabilities. The `--network none --cap-drop ALL` local smoke test intentionally limits permissions; it does not prove RouterOS compatibility.

**Do not import to CHR yet.** First validate local build and output. A later stage will export a tar archive and document RouterOS-specific import and rollback. A kernel NFQUEUE test requires explicit isolation and separate approval of network rule changes.
