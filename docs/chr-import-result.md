# CHR Docker archive import — verified 2026-11-04

After an OCI-layout `docker save` archive failed with `no config found in manifest`, the `skopeo copy --format v2s2 docker-daemon:... docker-archive:...` export imported successfully.

User-reported RouterOS 7.24.6 container details:

- State `S - STOPPED`, no extraction failure.
- `file=mikrotik-zapret2-routeros.tar`
- `tag=docker.io/library/mikrotik-zapret2:diagnostic`
- `os=linux`, `arch=amd64`, `privileged=no`
- `interface=veth-zapret`
- `default-entrypoint=/usr/local/bin/diagnose`
- `root-dir=/zapret-diag-002`, `layer-dir=/zapret-layers`
- `logging=yes`, `start-on-boot=no`
- `container-size=94.9MiB`

**Next verification:** run the inert diagnostic container and inspect RouterOS logs, including shared-library resolution and capability mask. Successful import does not establish that nfqws2 or NFQUEUE works.
