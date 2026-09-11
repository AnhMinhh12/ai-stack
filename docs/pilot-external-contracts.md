# Pilot external contracts

These controls are deliberately fail-closed. This repository contains no credentials,
certificate material, firewall changes, registry login, IdP configuration, or notification
endpoint.

## Secret manager and registry

The deployment job must resolve the following references from an approved secret manager,
then provide resolved values only through a protected runtime environment:

- `VLLM_API_KEY_REF`, `QDRANT_API_KEY_REF`, `REDIS_PASSWORD_REF`, `WEBUI_SECRET_KEY_REF`
- `OIDC_CLIENT_SECRET_REF`, `OIDC_CA_BUNDLE_REF`, `ALERT_WEBHOOK_REF`
- `OFFHOST_BACKUP_URI` for encrypted immutable storage

`SECRET_MANAGER_URI` and every `*_REF` must be non-empty, non-placeholder references.
The workspace cannot prove rotation, access policy, or off-host immutability; those require
dated evidence from Security/Operations. Registry requirements are in
[registry-release.md](registry-release.md).

## OIDC startup contract

Use the optional overlay only after Security provides an issuer, client, secret reference,
group claim mapping, redirect URL, and internal CA trust:

```bash
docker compose -f docker-compose.yml -f docker-compose.oidc.yml \
  --env-file /protected/oidc.env config --quiet
```

The overlay uses Open WebUI's `OPENID_PROVIDER_URL` and OAuth controls, disables OAuth
signup, group creation, role management, and email account merging. It refuses to render if
the issuer, client, client secret, or CA bundle path is absent. The IdP must register the
actual HTTPS redirect URL for the deployed gateway; this is checked by the contract checker
but cannot be tested without a real identity.

For the current company-wide shared-knowledge scope, manual internal accounts are the approved
temporary access model; public signup remains disabled. OIDC/group controls are deferred, and
restricted or segmented documents must not be uploaded until the IAM E2E matrix is completed.

## Observability and alerts

The gateway request ID is the correlation minimum. Retrieval/inference traces must use that ID,
redact prompt/document content and authorization headers, and store only a pseudonymous identity.
Langfuse connectivity, retention, alert notification delivery and on-call ownership are external
gates; `config/observability-contract.yaml` remains blocked until their values and evidence exist.

## Backup and clean room

`scripts/backup.sh` refuses to run without an encryption recipient/key. The clean-room verifier
requires an encrypted, complete backup and runs `restore.sh` only in `clean-room` mode before
inspecting a temporary isolated Docker volume. It never restores production containers, databases,
or volumes. Off-host immutable storage and named approval remain required before Bước 5 can pass.

