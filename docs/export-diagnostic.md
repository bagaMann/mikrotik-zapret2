# Stage 3: export local diagnostic image

On the Debian build VM:

```bash
cd /opt/mikrotik-zapret2
git pull --ff-only
bash scripts/export-diagnostic-image.sh
sha256sum -c out/mikrotik-zapret2-diagnostic.tar.sha256
```

This creates `out/mikrotik-zapret2-diagnostic.tar` from the **locally tested** image using `docker save`. No Docker Hub upload or registry pull is required.

**Gate:** first report the archive size, SHA-256, and the list of archive members. Do not import into RouterOS until the exact import procedure, filesystem paths, VETH configuration, and rollback are agreed. The container's entrypoint is read-only diagnostics, not packet manipulation.

Note: the image currently uses unpinned `debian:trixie-slim` and apt versions. Preserve the resulting image ID and archive SHA-256; a reproducible release still requires base-image and package pinning.
