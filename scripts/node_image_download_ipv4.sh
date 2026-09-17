#!/usr/bin/env bash
# Fetch the pinned Node image over IPv4 and load it locally for a Docker build.
set -euo pipefail
umask 077

ENV_FILE="${1:-release-image.env}"
[[ -f "${ENV_FILE}" ]] || { echo "[ERROR] Missing ${ENV_FILE}" >&2; exit 2; }
# release-image.env is maintained by the release workflow and contains only
# image assignments. Do not use it for arbitrary shell input.
NODE_IMAGE="$(awk -F= '$1 == "NODE_IMAGE" { print substr($0, index($0, "=") + 1); exit }' "${ENV_FILE}")"
[[ "${NODE_IMAGE}" == *@sha256:* ]] || { echo "[ERROR] NODE_IMAGE must be pinned by digest" >&2; exit 2; }

REFERENCE="${NODE_IMAGE%@*}"
DIGEST="${NODE_IMAGE#*@}"
IMAGE_NAME="${REFERENCE%%:*}"
TAG="${REFERENCE#*:}"
REPOSITORY="library/${IMAGE_NAME}"
case "$(uname -m)" in
  aarch64|arm64) ARCH=arm64 ;;
  x86_64|amd64) ARCH=amd64 ;;
  *) echo "[ERROR] Unsupported architecture: $(uname -m)" >&2; exit 2 ;;
esac

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT
token="$(curl -4 -fsSL "https://auth.docker.io/token?service=registry.docker.io&scope=repository:${REPOSITORY}:pull" | python3 -c 'import json,sys; print(json.load(sys.stdin)["token"])')"
headers=(-H "Authorization: Bearer ${token}")
fetch() { curl -4 -fsSL "${headers[@]}" "$1"; }
verify() {
  local file="$1" expected="$2" actual
  actual="sha256:$(sha256sum "${file}" | awk '{print $1}')"
  [[ "${actual}" == "${expected}" ]] || { echo "[ERROR] Digest mismatch: ${file}" >&2; exit 2; }
}

mkdir -p "${WORK}/blobs/sha256"
fetch "https://registry-1.docker.io/v2/${REPOSITORY}/manifests/${DIGEST}" > "${WORK}/index.source.json"
verify "${WORK}/index.source.json" "${DIGEST}"
child="$(python3 - "${WORK}/index.source.json" "${ARCH}" <<'PY'
import json, sys
for item in json.load(open(sys.argv[1])).get("manifests", []):
    platform = item.get("platform", {})
    if platform.get("os") == "linux" and platform.get("architecture") == sys.argv[2]:
        print(item["digest"])
        break
else:
    raise SystemExit("no matching Linux architecture in image index")
PY
)"
manifest="${WORK}/blobs/sha256/${child#sha256:}"
fetch "https://registry-1.docker.io/v2/${REPOSITORY}/manifests/${child}" > "${manifest}"
verify "${manifest}" "${child}"
mapfile -t blobs < <(python3 - "${manifest}" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
print(data["config"]["digest"])
for layer in data["layers"]:
    print(layer["digest"])
PY
)
for blob in "${blobs[@]}"; do
  output="${WORK}/blobs/sha256/${blob#sha256:}"
  fetch "https://registry-1.docker.io/v2/${REPOSITORY}/blobs/${blob}" > "${output}"
  verify "${output}" "${blob}"
done
printf '{"imageLayoutVersion":"1.0.0"}\n' > "${WORK}/oci-layout"
size="$(stat -c %s "${manifest}")"
python3 - "${WORK}/index.json" "${child}" "${size}" "${REFERENCE}" <<'PY'
import json, sys
json.dump({"schemaVersion": 2, "manifests": [{
    "mediaType": "application/vnd.oci.image.manifest.v1+json",
    "digest": sys.argv[2], "size": int(sys.argv[3]),
    "annotations": {"org.opencontainers.image.ref.name": sys.argv[4]},
}]}, open(sys.argv[1], "w"), separators=(",", ":"))
PY

archive="${NODE_IMAGE_ARCHIVE:-/tmp/htmp-node-image.tar}"
[[ ! -e "${archive}" ]] || { echo "[ERROR] Archive already exists: ${archive}" >&2; exit 2; }
skopeo copy --override-os linux --override-arch "${ARCH}" "oci:${WORK}:${REFERENCE}" "docker-archive:${archive}:${REFERENCE}"
docker load --input "${archive}"
docker image inspect "${REFERENCE}" >/dev/null
echo "Node image load: PASS (${REFERENCE}; source ${DIGEST})"
