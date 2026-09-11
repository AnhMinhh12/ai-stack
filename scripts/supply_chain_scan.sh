#!/usr/bin/env bash
set -euo pipefail
: "${IMAGE:?Set IMAGE to an immutable image@sha256 reference}"
: "${EVIDENCE_DIR:?Set EVIDENCE_DIR to docs/evidence/REL-<id>}"
: "${SYFT_IMAGE:?Set SYFT_IMAGE to a pinned syft image@sha256 reference}"
: "${GRYPE_IMAGE:?Set GRYPE_IMAGE to a pinned grype image@sha256 reference}"
case "${IMAGE}" in *@sha256:*) ;; *) echo "FAIL CLOSED: IMAGE must include @sha256 digest" >&2; exit 2;; esac
case "${SYFT_IMAGE}" in *@sha256:*) ;; *) echo "FAIL CLOSED: SYFT_IMAGE must be pinned" >&2; exit 2;; esac
case "${GRYPE_IMAGE}" in *@sha256:*) ;; *) echo "FAIL CLOSED: GRYPE_IMAGE must be pinned" >&2; exit 2;; esac
mkdir -p "${EVIDENCE_DIR}"
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "${PWD}/${EVIDENCE_DIR}:/out" "${SYFT_IMAGE}" "${IMAGE}" -o spdx-json=/out/sbom.spdx.json -o cyclonedx-json=/out/sbom.cdx.json
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "${PWD}/${EVIDENCE_DIR}:/out" "${GRYPE_IMAGE}" "sbom:/out/sbom.spdx.json" -o json > "${EVIDENCE_DIR}/cve.grype.json"
python3 - "${EVIDENCE_DIR}/sbom.spdx.json" "${EVIDENCE_DIR}/licenses.json" <<'PY'
import json,sys
sbom=json.load(open(sys.argv[1]))
packages=[{"name":p.get("name"),"version":p.get("versionInfo"),"license":p.get("licenseConcluded")} for p in sbom.get("packages",[])]
json.dump({"packages":packages},open(sys.argv[2],"w"),indent=2)
PY
