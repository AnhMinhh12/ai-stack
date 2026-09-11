# Single-host lightweight OCI Registry

This replaces Harbor for the current one-server deployment. It is an OCI/Docker Distribution registry, not a public service.
It binds only to `127.0.0.1:5443`; users of Open WebUI never access it. It still requires TLS, basic authentication and protected persistent storage.

## Current implementation

The Registry is running locally at `https://localhost:5443`, with TLS, basic authentication, a dedicated local Robot Account and persistent storage outside Git. It is healthy and does not expose a LAN/public port. The source Registry image was fetched through IPv4 and checksum-verified because the Docker daemon has no IPv6 route to Docker Hub.

The currently running Open WebUI image has been pushed as the rollback baseline and verified by digest:

```text
localhost:5443/ai/open-webui-htmp@sha256:9b03fd56826d76cd503a5f4c126db919537dc5ea7490265fdd5bb12c6ba63cdd
```

Set this for future release builds on this host:

```bash
export HTMP_REGISTRY=localhost:5443
```

The generated CA, Registry key and Robot Account credential are in the ignored, mode-restricted `.secrets/registry/` directory; their values must not be copied into Git, evidence or chat. `scripts/registry_download_ipv4.sh` provides the IPv4/checksum/bootstrap path for a replacement image.

## Limits

This is single-host storage, so it does not protect against host/disk loss. Keep encrypted off-host copies of release evidence and backup archives. It is adequate for local image reproducibility/rollback, not HA or disaster recovery.

