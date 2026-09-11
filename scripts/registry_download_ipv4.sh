#!/usr/bin/env bash
# Download the approved Registry image over IPv4 and load it into Docker without changing daemon DNS.
set -euo pipefail
umask 077

INDEX_DIGEST="sha256:a3d8aaa63ed8681a604f1dea0aa03f100d5895b6a58ace528858a7b332415373"
LOCAL_TAG="htmp/registry-service:sha-a3d8aaa63ed8681a604f1dea0aa03f100d5895b6a58ace528858a7b332415373"
REPOSITORY="library/registry"
ARCH="arm64"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

token="$(curl -4 -fsSL "https://auth.docker.io/token?service=registry.docker.io&scope=repository:${REPOSITORY}:pull" | python3 -c 'import json,sys; print(json.load(sys.stdin)["token"])')"
headers=(-H "Authorization: Bearer ${token}")
fetch() { curl -4 -fsSL "${headers[@]}" "$1"; }
verify() {
  local file="$1" digest="$2" actual
  actual="sha256:$(sha256sum "${file}" | awk '{print $1}')"
  [[ "${actual}" == "${digest}" ]] || { echo "[ERROR] Digest mismatch: expected ${digest}, got ${actual}" >&2; exit 2; }
}

mkdir -p "${WORK}/blobs/sha256"
fetch "https://registry-1.docker.io/v2/${REPOSITORY}/manifests/${INDEX_DIGEST}" > "${WORK}/index.source.json"
verify "${WORK}/index.source.json" "${INDEX_DIGEST}"
child="$(python3 - "${WORK}/index.source.json" "${ARCH}" <<'PY'
import json, sys
data=json.load(open(sys.argv[1]))
arch=sys.argv[2]
for item in data.get("manifests", []):
    p=item.get("platform", {})
    if p.get("os") == "linux" and p.get("architecture") == arch:
        print(item["digest"]); break
else:
    raise SystemExit("no linux/%s manifest" % arch)
PY
)"
child_hex="${child#sha256:}"
manifest="${WORK}/blobs/sha256/${child_hex}"
fetch "https://registry-1.docker.io/v2/${REPOSITORY}/manifests/${child}" > "${manifest}"
verify "${manifest}" "${child}"
mapfile -t blobs < <(python3 - "${manifest}" <<'PY'
import json, sys
data=json.load(open(sys.argv[1]))
print(data["config"]["digest"])
for layer in data["layers"]: print(layer["digest"])
PY
)
for blob in "${blobs[@]}"; do
  hex="${blob#sha256:}"
  out="${WORK}/blobs/sha256/${hex}"
  fetch "https://registry-1.docker.io/v2/${REPOSITORY}/blobs/${blob}" > "${out}"
  verify "${out}" "${blob}"
done
printf '{"imageLayoutVersion":"1.0.0"}\n' > "${WORK}/oci-layout"
size="$(stat -c %s "${manifest}")"
python3 - "${WORK}/index.json" "${child}" "${size}" <<'PY'
import json, sys
path, digest, size = sys.argv[1], sys.argv[2], int(sys.argv[3])
json.dump({"schemaVersion":2,"manifests":[{"mediaType":"application/vnd.oci.image.manifest.v1+json","digest":digest,"size":size,"annotations":{"org.opencontainers.image.ref.name":"registry"}}]}, open(path,"w"), separators=(",", ":"))
PY
archive="${REGISTRY_ARCHIVE:-/tmp/htmp-registry-service.tar}"
[ ! -e "${archive}" ] || { echo "[ERROR] Archive already exists: ${archive}" >&2; exit 2; }
skopeo copy --override-os linux --override-arch "${ARCH}" "oci:${WORK}:registry" "docker-archive:${archive}:${LOCAL_TAG}"
docker load --input "${archive}"
docker image inspect "${LOCAL_TAG}" >/dev/null
echo "Registry image load: PASS (${LOCAL_TAG}; source ${INDEX_DIGEST})"

