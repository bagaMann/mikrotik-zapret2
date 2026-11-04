# Stage 1 — official-source binary build (not an OCI image yet)

Upstream: https://github.com/bol-van/zapret2

The upstream `nfq2` Makefile builds `nfqws2` for Linux. Its documented Debian build dependencies include `make gcc zlib1g-dev libcap-dev libnetfilter-queue-dev libmnl-dev libluajit-5.1-dev`; `libsystemd-dev` is needed only for a systemd-enabled build. Confirm dependency names on the selected Debian release.

On a disposable Debian amd64 VM:

```bash
sudo apt-get update
sudo apt-get install -y git make gcc file zlib1g-dev libcap-dev libnetfilter-queue-dev libmnl-dev libluajit-5.1-dev
git clone https://github.com/bagaMann/mikrotik-zapret2.git
cd mikrotik-zapret2
# First audit and select an actual upstream commit SHA; do not use moving master:
ZAPRET2_COMMIT=<40-hex-audited-sha> bash scripts/build-nfqws2-debian.sh
```

Outputs: `out/nfqws2`, `out/nfqws2.sha256`, `out/upstream-commit.txt`, `out/help.txt`.

**Not yet done:** selecting and auditing an upstream commit; executing this build; constructing an OCI image; proving NFQUEUE access from RouterOS VETH. Do not claim a successful build or compatibility until tested.

**Architecture caveat:** RouterOS containers are Linux userspaces connected through VETH; they do not grant control over the RouterOS host firewall. Linux NFQUEUE in a container is not equivalent to RouterOS packet interception. Any routing and queueing must be validated in a disposable CHR lab before enabling production traffic.

Next: pin upstream revision and base image digest, inspect `nfq2/Makefile`, determine kernel capabilities available to the container, then implement minimal runtime image and test harness.
