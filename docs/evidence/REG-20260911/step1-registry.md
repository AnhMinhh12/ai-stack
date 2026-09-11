# REG-20260911 — single-host OCI Registry preparation

**UTC:** 2026-09-11T03:10:49Z  
**Owner:** Ho Anh Minh  
**Status:** `blocked` — registry image is not available on the server.

## Implemented

- Added `docker-compose.registry.yml` using an immutable Docker Distribution image digest, TLS, htpasswd authentication, protected data mount, deletion policy and loopback-only port `127.0.0.1:5443`.
- Added `registry/config.yml`, offline image import verifier and operating guide.
- Registry remains separate from Open WebUI ports `80/443`; it is intended only for local build/deploy on this single host.

## Checks

- No local Registry image existed.
- Attempting to pull the official pinned Registry image failed: the server has no route to Docker Hub (`network is unreachable`).
- Shell syntax and Compose rendering passed with non-secret placeholder paths.
- Offline import script rejects a missing archive with exit code `2`.
- No Registry container, certificate, credential, storage directory, DNS entry or firewall rule was created.

## Required handoff

On an approved connected machine, pull and save the exact image named in `docs/single-host-oci-registry.md`, transfer the archive through an approved internal channel, and provide a checksum. Before start, the operator must create TLS/auth/data directories outside Git and schedule Docker CA trust/restart. Off-host backup remains a separate gate.

**Expiry:** 2026-09-25T03:10:49Z or on a change to the Registry digest/configuration.



## Superseding implementation update — 2026-09-11T06:34:45Z

**Status:** `partial — Registry and rollback baseline pass; full release gate remains blocked`.

- Installed `skopeo` using operator-provided sudo authorization; no AI container restart occurred.
- Docker/Skopeo could not use the server DNS IPv6 route, so the approved public Registry image was fetched over IPv4 via OCI API. The OCI index, arm64 manifest and every config/layer blob were SHA-256 verified before loading the local image.
- Created a local CA/certificate for `localhost`, protected Registry storage outside Git, and a dedicated random Robot Account credential under ignored/mode-restricted `.secrets/registry/`. Values were not printed.
- Started the Registry at `127.0.0.1:5443`; TLS/authenticated API, Docker login and auth-aware healthcheck pass.
- Pushed the current Open WebUI image, then pulled it back by digest: `localhost:5443/ai/open-webui-htmp@sha256:9b03fd56826d76cd503a5f4c126db919537dc5ea7490265fdd5bb12c6ba63cdd`.

The Registry is single-host only. SBOM/CVE/license artifacts, signed Git tag, Security approval, candidate custom-image build and staging rollback test remain required before release promotion.
