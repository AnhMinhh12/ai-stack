# OCI registry và quy trình phát hành

## Triển khai hiện tại: registry một máy

Registry hiện là OCI/Docker Distribution chạy riêng trên host, không phải dịch
vụ công cộng. Nó chỉ bind `127.0.0.1:5443`, dùng TLS, basic authentication,
Robot Account cục bộ và persistent storage ngoài Git; người dùng Open WebUI
không truy cập trực tiếp.

Open WebUI rollback baseline đang có digest:

```text
localhost:5443/ai/open-webui-htmp@sha256:9b03fd56826d76cd503a5f4c126db919537dc5ea7490265fdd5bb12c6ba63cdd
```

Thiết lập build trên host này:

```bash
export HTMP_REGISTRY=localhost:5443
```

CA, private key và credential Robot Account nằm trong
`.secrets/registry/` (ignored, mode-restricted), không sao chép vào Git, chat
hay evidence. `scripts/registry_download_ipv4.sh` là đường bootstrap có
checksum khi Docker daemon không có IPv6 egress.

Registry một máy chỉ đáp ứng reproducibility/rollback cục bộ; không thay thế
backup off-host, HA hay DR.

For a networked/central release, images are published only to
`registry.htmp.internal/ai/open-webui-htmp`. The registry implementation is
Harbor or an OCI-compatible service with equivalent TLS, audit, retention,
backup, and RBAC controls.

## Required platform controls

- DNS: `registry.htmp.internal` resolves only from the approved build and deployment networks.
- TLS: certificate is issued by the internal CA and trusted by Docker hosts.
- RBAC: a Robot Account has push/pull scope limited to project `ai`; deployments use pull-only credentials.
- Retention: retain the approved release and its rollback baseline digests; enable immutable tags and audit logs.
- Backup: registry metadata and blob storage are included in the Operations backup policy.

## Release operator flow

1. Provision DNS, CA trust, Harbor project `ai`, and Robot Account outside this repository.
2. Copy `.env.release.example` into the protected release environment and authenticate Docker to the registry.
3. Run `scripts/build_release_image.sh`; record the generated digest in the release manifest.
4. Run `scripts/bootstrap_openwebui_rag.py --owner-email "$OPENWEBUI_BOOTSTRAP_OWNER_EMAIL" --apply`.
5. Run `IMAGE=<image@digest> EVIDENCE_DIR=docs/evidence/REL-<id> scripts/supply_chain_scan.sh`.
6. Security reviews the policy and writes its signed approval/exception evidence.
7. Run `scripts/release_gate.py`. A nonzero exit code blocks promotion.
