# NFQUEUE registration probe (CHR lab only)

The diagnostic container ran successfully on RouterOS 7.24.6, but this does **not** prove NFQUEUE support. This second image opens a libnetfilter_queue handle and attempts to register queue 49152, then immediately destroys the queue and closes the handle. It does not add firewall rules, set packet marks, or route traffic. Queue 49152 must not be in use by another process.

## Build on Debian
```sh
cd /opt/mikrotik-zapret2
git pull --ff-only
bash scripts/build-nfqueue-probe.sh
sha256sum -c out/mikrotik-zapret2-nfqueue-probe.tar.sha256
scp -i /root/.ssh/chr_zapret_ed25519 -o IdentitiesOnly=yes out/mikrotik-zapret2-nfqueue-probe.tar admin@192.168.11.220:mikrotik-zapret2-nfqueue-probe.tar
```

## CHR
```routeros
/container add file=mikrotik-zapret2-nfqueue-probe.tar interface=veth-zapret root-dir=zapret-probe-001 logging=yes start-on-boot=no comment="Zapret2 NFQUEUE bind-only probe"
/container print detail
/container start [find where comment="Zapret2 NFQUEUE bind-only probe"]
/log print without-paging where topics~"container"
/container print detail
```

The probe exits immediately, with 0 on successful queue bind/release, 10 if opening NFQUEUE fails, 11 if queue registration fails. No packets are queued because the probe does not install any firewall rules. A successful registration is **not** proof of interception support. Inspect kernel errors and follow up with an isolated packet test before making any forwarding changes.

**Caution:** the CHR diagnostic reported an unusually broad effective capability mask, even with `privileged=no`. Do not expose this test container to untrusted workloads.
