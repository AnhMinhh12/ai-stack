#!/usr/bin/env bash
set -euo pipefail
: "${HTMP_REGISTRY:?Set HTMP_REGISTRY, e.g. registry.htmp.internal}"
: "${HTMP_REGISTRY_NAMESPACE:=ai}"
: "${NODE_IMAGE:?Set NODE_IMAGE to node@sha256:...}"
case "${NODE_IMAGE}" in *@sha256:*) ;; *) echo "FAIL CLOSED: NODE_IMAGE must be immutable" >&2; exit 2;; esac
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "FAIL CLOSED: build only from a clean, committed worktree" >&2
  exit 2
fi
commit="$(git rev-parse --verify HEAD)"
short_commit="$(git rev-parse --short=12 HEAD)"
image="${HTMP_REGISTRY}/${HTMP_REGISTRY_NAMESPACE}/open-webui-htmp"
tag="git-${short_commit}"
docker buildx build --platform linux/arm64 --provenance=true --sbom=true --push   --build-arg NODE_IMAGE="${NODE_IMAGE}"   --build-arg BUILD_HASH="${commit}"   --tag "${image}:${tag}"   --file Dockerfile.openwebui-speed-runtime .
digest="$(docker buildx imagetools inspect "${image}:${tag}" --format '{{.Digest}}')"
test -n "${digest}"
printf 'HTMP_OPEN_WEBUI_IMAGE=%s@%s\nNODE_IMAGE=%s\n' "${image}" "${digest}" "${NODE_IMAGE}" > release-image.env
echo "Published ${image}@${digest}"
