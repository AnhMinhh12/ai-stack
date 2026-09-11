# Company-wide shared-knowledge scope

**Effective:** 2026-09-11  
**Owner:** Ho Anh Minh  
**Status:** approved scope decision — detailed RBAC/OIDC deferred, not removed.

## Current access model

- The current deployment serves one company-wide internal knowledge scope; every approved internal account may query the same knowledge bases.
- Public self-signup remains disabled by the immutable Compose setting `ENABLE_SIGNUP=False`. Accounts are created, disabled and removed manually by the administrator until OIDC is introduced.
- The optional `docker-compose.oidc.yml` overlay remains disabled and is not part of the current deployment.
- This is not a permission boundary. Do not upload HR, payroll, legal, personal-data, customer-restricted, financial, security-sensitive or other documents that need department/person-level access control.

## Required minimum operations

- Maintain an account inventory with creator, employee/contractor status and disable date; remove access when employment ends.
- Keep source documents limited to the approved company-wide internal classification.
- Preserve request correlation and redacted operational logs; do not record prompts, source text, auth headers or credentials in custom observability metadata.
- Treat a need to upload restricted data as a trigger to implement OIDC/group mapping and source-level RAG authorization before upload.

## Deferred work

OIDC, MFA, group mapping, access review and RAG ACL verification are explicitly deferred. They are no longer a prerequisite for the shared-knowledge rollout, but remain mandatory before introducing restricted or segmented knowledge.

