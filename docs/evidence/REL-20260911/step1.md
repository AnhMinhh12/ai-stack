# REL-20260911 -- Step 1 implementation evidence

**Test ID:** REL-20260911-STEP1-TOOLING  
**Owner:** Ho Anh Minh  
**Approver:** Security  
**Status:** blocked

## Implemented

- Reproducible Open WebUI Dockerfile: immutable upstream base, pinned upstream source revision, and release-time Node base image digest.
- Versioned, idempotent Open WebUI RAG bootstrap for HTMP Nhanh and HTMP Ky.
- Private-registry release instructions, immutable-image build helper, SBOM/CVE/license scanner wrapper, evidence templates, and fail-closed release gate.

## Verification

- Python bootstrap/release scripts compile.
- Shell release scripts pass bash syntax validation.
- Docker Compose config passes using the local lab image variable.
- Bootstrap apply/check passes against the live Open WebUI instance.
- All eight runtime services are healthy.
- Release gate blocks the template because no registry digest, scan results, Security approval, or signed release tag exists.

## Remaining blockers

The private registry registry.htmp.internal, internal CA trust, Robot Account, pinned Node/scanner digests, scan artifacts, Security approval, immutable release tag, and verified rollback baseline do not yet exist in this workspace. The build validation cannot pull Docker Hub metadata because this host has no egress to it. This is implementation evidence, not promotion evidence.
