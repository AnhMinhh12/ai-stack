# PILOT-20260911 — Bước 0–7 implementation evidence

**UTC:** 2026-09-11T03:06:49Z  
**Revision under test:** `85bdb0cfdb3bb69716110465c485194e23f2fcbf` (worktree contains the implementation changes documented here)  
**Scope:** workspace controls and live staging smoke only; no external deployment, GPU load, production restore, or traffic promotion.  
**Status:** `blocked` — expected fail-closed external/approval gates remain open.

## Completed, verified workspace controls

- Bước 1: reproducible Open WebUI build/release helpers, SBOM/CVE/license wrapper, versioned RAG bootstrap, immutable-digest release gate, and registry/rollback templates exist. The gate rejects the incomplete template: manifest digest, approval status and scan artifacts are all `BLOCKED` (exit `2`).
- Bước 2: `config/pilot-contract.env.example` and `scripts/pilot_contract_check.py` require external secret-manager references, alert/on-call metadata, retention, and off-host backup location. An empty contract exits `2`; no secret value was read or recorded.
- Bước 3: `docker-compose.oidc.yml` is an optional Open WebUI OIDC overlay. It refuses missing issuer/client/secret/CA inputs; a synthetic, non-secret rendering passed `docker compose ... config --quiet`. `scripts/iam_e2e_matrix.py` exits `2` until two real test identities/groups and base URL exist.
- Bước 4: observability requirements are captured in `config/observability-contract.yaml` and checked through the contract checker. Both RAG filters carry only an opaque request ID and retrieval profile in metadata; they do not copy prompt, source text, auth headers, email or credentials. Gateway request correlation already exists; Langfuse trace delivery, redaction enforcement, notification endpoint, retention and on-call remain external gates.
- Bước 5: `scripts/clean_room_verify.sh` accepts only a completed backup below `backups/backup_*`, runs `restore.sh` in `RESTORE_MODE=clean-room`, and uses a temporary Docker volume. With no GPG recipient it fails closed before reading/decrypting (`exit 2`). No backup or restore was performed.
- Bước 6: `python3 scripts/benchmark_vllm.py` dry-run enumerated the 48-case workload matrix without GPU load. The actual matrix and 24-hour soak remain locked pending an approved window, workload, SLO/headroom and abort thresholds.
- Bước 7: `python3 scripts/staging_smoke_check.py` passed: Compose config, eight healthy services, Nginx, Open WebUI, authenticated vLLM/Qdrant, Tika, Langfuse, versioned bootstrap, and both RAG profiles/citations.

## Commands and results

```text
bash -n scripts/{backup,restore,clean_room_verify,build_release_image,supply_chain_scan}.sh                 PASS
python3 -m py_compile scripts/{pilot_contract_check,iam_e2e_matrix,staging_smoke_check,rag_profile_check,bootstrap_openwebui_rag,openwebui_bootstrap_runtime}.py functions/{htmp_fast_rag,htmp_technical_rag}.py   PASS
env -i ... python3 scripts/pilot_contract_check.py --strict --oidc                                     BLOCKED (exit 2, expected)
env -i ... python3 scripts/iam_e2e_matrix.py                                                           BLOCKED (exit 2, expected)
env -i ... scripts/clean_room_verify.sh <existing backup>                                              BLOCKED (exit 2: no GPG recipient, expected)
synthetic OIDC docker compose overlay render                                                            PASS
python3 scripts/rag_profile_check.py                                                                    PASS
python3 scripts/staging_smoke_check.py                                                                  PASS
python3 scripts/release_gate.py --manifest docs/evidence/REL-TEMPLATE/release-manifest.yaml ...        BLOCKED (exit 2, expected)
git diff --check                                                                                        PASS
```

## Remaining external handoffs (all gates remain blocked)

- Internal registry DNS/CA/Robot Account plus pinned scanner images, immutable image digest, scan artifacts, signed tag and Security approval.
- Secret manager, formal rotation evidence, off-host immutable encrypted backup destination and named approver.
- OIDC issuer/client secret/group claims/test identities/MFA, firewall/VPN/TLS validation, alert endpoint and on-call owner.
- Approved GPU workload window, SLO/headroom and abort thresholds; full 48-case run and 24-hour soak.
- Clean-room Compose environment, valid encrypted backup, named DR approval, recovery validation for WebUI records, Qdrant vectors, files and sample RAG.

**Final runtime recheck (UTC 2026-09-11T03:10:49Z):** Bootstrap apply/check, RAG-profile check, staging smoke and `git diff --check` all passed after the request-ID hook update.

**Expiry:** This evidence is implementation-only and expires on any change to release image, model/embedding revision, schema, RAG bootstrap, secret/OIDC/alert/backup contract, or after 14 days (2026-09-25T03:06:49Z).

