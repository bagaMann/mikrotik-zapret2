# Upstream candidate (not yet audited)

Candidate full SHA: `4080df37c4d1ab70acb527a63a575954e72974e3` from official `bol-van/zapret2` commit history. **Candidate only**: review source and dependencies before accepting as trusted release.

Inspected upstream `nfq2/Makefile`: default Linux target `nfqws2`; Linux libraries `-lz -lnetfilter_queue -lnfnetlink -lmnl -lm`; LuaJIT is enabled by default (`LUA_JIT=1`), fallback to Lua may happen if LuaJIT is missing. Our script explicitly requests LuaJIT, but dependency validation is still required.

Debian 13 build prerequisites:

```bash
apt update
apt install -y git make gcc pkg-config file zlib1g-dev libcap-dev libnetfilter-queue-dev libnfnetlink-dev libmnl-dev libluajit-5.1-dev
```

Build after reviewing candidate:

```bash
cd /opt/mikrotik-zapret2
git pull --ff-only
ZAPRET2_COMMIT=4080df37c4d1ab70acb527a63a575954e72974e3 bash scripts/build-nfqws2-debian.sh
file out/nfqws2
ldd out/nfqws2
cat out/nfqws2.sha256
```

This compiles a native Debian binary only, **not** an OCI image. Dynamic libraries from Debian cannot be assumed available in a minimal RouterOS container. No packet processing or NFQUEUE tests have been performed yet.
