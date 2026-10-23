#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="$repo_root/open-webui-dev"
source_rev=d3e8bf3405e848cfba377814d0aa7ba7290e414d

if [[ -e "$source_dir" ]]; then
  if [[ ! -f "$source_dir/package.json" ]]; then
    echo "Existing $source_dir is not an Open WebUI checkout" >&2
    exit 1
  fi
  echo "Using existing checkout: $source_dir"
else
  git init "$source_dir"
  git -C "$source_dir" remote add origin https://github.com/open-webui/open-webui.git
  git -C "$source_dir" fetch --depth 1 origin "$source_rev"
  git -C "$source_dir" checkout --detach FETCH_HEAD
  test "$(git -C "$source_dir" rev-parse HEAD)" = "$source_rev"

  cd "$source_dir"
  selector="$(find src -type f -path '*/ModelSelector.svelte' -print -quit)"
  test -n "$selector"
  perl "$repo_root/scripts/patch_openwebui_speed_selector.pl" "$selector"
  perl "$repo_root/scripts/patch_openwebui_branding.pl" "$repo_root/assets/htmp-logo.png"
  perl "$repo_root/scripts/patch_openwebui_erp_scroll.pl" src/lib/components/chat/Chat.svelte
fi

# This pinned upstream revision puts TypeScript generics in a JavaScript
# module script. Vite's dependency scanner rejects it until lang is explicit.
file_nav="$source_dir/src/lib/components/chat/FileNav.svelte"
if [[ "$(head -n 1 "$file_nav")" == '<script context="module">' ]]; then
  sed -i '1s/<script context="module">/<script context="module" lang="ts">/' "$file_nav"
fi

python3 "$repo_root/scripts/patch_openwebui_employee_login.py" \
  "$source_dir/src/routes/auth/+page.svelte"

echo "Source ready at $source_dir"
