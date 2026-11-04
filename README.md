# mikrotik-zapret2

Reproducible, security-reviewed experiment to run the **official** [bol-van/zapret2](https://github.com/bol-van/zapret2) on MikroTik RouterOS CHR using an independently built OCI image.

> **Status: research / bootstrap only. No working container or RouterOS integration is claimed yet. Do not deploy on a production router.**

## Goals

- Pin upstream source to an audited full Git commit SHA; never pull unreviewed code at runtime.
- Pin base images by digest and record all build dependencies.
- Build for `linux/amd64` first; investigate `arm64` separately.
- Prefer a minimal image, no package manager or update agent in the runtime stage.
- Verify what network capabilities and packet-processing mode RouterOS containers actually support before writing routing rules.
- Route only an isolated test client, with a documented rollback and no changes to existing BGP/VPN routing.
- Keep checksums, SBOM, build logs, test results, and RouterOS version compatibility notes.

## Lab baseline (2026-11-04)

| Property | Observed |
|---|---|
| Hypervisor | Proxmox / QEMU |
| RouterOS | 7.21.5 long-term |
| Platform | CHR x86_64 |
| CPU | 1 vCPU (recommend 2 for lab) |
| RAM | 1024 MiB |
| Disk | 89.2 MiB total, 69.6 MiB free (**insufficient**) |
| `container` package | not installed |
| Device mode | advanced; `container=no` |

## Stage gates

1. **Lab storage and console**: enlarge disk to 2–4 GiB; verify usable space in RouterOS; confirm Proxmox console access.
2. **RouterOS support**: install exact matching official container package and enable device-mode container using MikroTik's documented physical/console confirmation procedure.
3. **Source audit**: inspect official Zapret2 source, build flags, dependencies, and RouterOS-specific packet path; pin revisions.
4. **Build and static tests**: create reproducible Dockerfile, manifest/SBOM and test scripts.
5. **Linux integration**: validate packet handling in an isolated Linux namespace/VM before CHR.
6. **CHR integration**: isolated VETH and test client, packet captures, failure tests, explicit rollback.
7. **Production candidate**: only after user confirms functional and stability tests.

## Security policy

- No third-party prebuilt nfqws2 image is trusted as a runtime dependency.
- No `curl | sh`, unattended upstream downloads, or privileged management API credentials inside the container.
- No RouterOS routing changes before a tested fail-safe design.
- Build and deployment artifacts must be traceable to exact commits and hashes.
- Failures must be reported as failures, not silently bypassed.

## References

- [Zapret2 upstream](https://github.com/bol-van/zapret2)
- [MikroTik Container documentation](https://help.mikrotik.com/docs/spaces/ROS/pages/84901929/Container)

Documentation and code will be added incrementally after each stage is verified.
