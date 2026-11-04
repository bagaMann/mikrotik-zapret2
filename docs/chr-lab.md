# Verified CHR lab — 2026-11-04

RouterOS 7.24.6 long-term, x86_64 QEMU, 2 vCPU, 1024 MiB RAM, 4161.4 MiB disk (4140.1 MiB free).

Package `container` version 7.24.6 is installed. Device mode `advanced` reports `container: yes`, `flagged: no`, `attempt-count: 0`. `/container/print` is empty. `/container/config/print` shows unset `layer-dir` and `tmpdir`; no image imported yet.

Next gate: audit upstream Zapret2 packet capture mode and determine whether RouterOS VETH transit traffic can be processed using Linux NFQUEUE inside the container. No operational compatibility claim yet. Build from pinned official upstream commit; do not use third-party binary images or runtime auto-downloads.

Reference: https://help.mikrotik.com/docs/spaces/ROS/pages/84901929/Container
