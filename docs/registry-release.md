# Private OCI registry and release procedure

Release images are published only to `registry.htmp.internal/ai/open-webui-htmp`.
The registry implementation is Harbor or an OCI-compatible service with equivalent
TLS, audit, retention, backup, and RBAC controls.

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
