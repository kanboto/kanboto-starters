#!/usr/bin/env bash
# Copies the images listed in $IMAGES to $MIRROR with crane, manifests intact (multi-arch index included, so a
# copy keeps the upstream digest), then writes $OUT. One image per line: `<source> <name:tag> [<owner/repo>]`.
# - With a GitHub repository, the source is a tool: its tag is the repository's latest stable release (as is,
#   or without its leading `v`), copied under that version and under the mirror tag (`stable`).
# - Without, the source carries its tag (`postgres:17-alpine`), copied as is.
# A copy is skipped when the mirror already holds the upstream digest; each call is retried with backoff.
set -euo pipefail

mirror=${MIRROR:?MIRROR is required}
attempts=${ATTEMPTS:-10}
delay=${DELAY:-15}
max_delay=${MAX_DELAY:-300}
out=${OUT:-GHCR.md}
today=$(date -u +%Y-%m-%d)
ref='^[a-z0-9][a-z0-9._/-]*(:[A-Za-z0-9._-]+)?$'

with_retry() {
  local wait=$delay attempt
  for attempt in $(seq 1 "$attempts"); do
    if "$@"; then return 0; fi
    if [ "$attempt" -lt "$attempts" ]; then
      echo "Attempt $attempt/$attempts failed, retrying in ${wait}s" >&2
      sleep "$wait"
      wait=$((wait * 2 > max_delay ? max_delay : wait * 2))
    fi
  done
  return 1
}

latest_release() {
  local auth=()
  if [ -n "${GITHUB_TOKEN:-}" ]; then auth=(-H "Authorization: Bearer $GITHUB_TOKEN"); fi
  curl -fsSL "${auth[@]}" -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/$1/releases/latest" |
    python3 -c 'import json, sys; print(json.load(sys.stdin)["tag_name"])'
}

# The image tag of a release: as is (`v2.15.1`), or without its leading `v` (`0.75.0`).
image_tag() {
  if crane digest "$1:$2" >/dev/null; then echo "$2"; else crane digest "$1:${2#v}" >/dev/null && echo "${2#v}"; fi
}

copy() {
  local src=$1 dst=$2 upstream
  upstream=$(crane digest "$src") || return 1
  if [ "$(crane digest "$dst" 2>/dev/null || true)" = "$upstream" ]; then
    echo "$dst already at $upstream"
    return 0
  fi
  crane copy "$src" "$dst"
}

# Date the digest was first mirrored, read from the previous table: an unchanged image keeps its date.
since() {
  [ -f "$out" ] || return 0
  awk -F' \\| ' -v m="$1" -v d="\`$2\`" 'index($2, m) == 1 && $3 == d { sub(/ \|$/, "", $4); print $4; exit }' "$out"
}

mirror_one() {
  local source=$1 target=$2 repo=${3:-} version src dst tags digest date
  if [ -n "$repo" ]; then
    version=$(with_retry latest_release "$repo") || return 1
    [[ "$version" =~ ^v?[0-9]+(\.[0-9]+)*$ ]] || { echo "unexpected release tag: $version" >&2; return 1; }
    version=$(with_retry image_tag "$source" "$version") || return 1
    src="$source:$version"
    dst="$mirror/${target%%:*}:$version"
    with_retry copy "$src" "$dst" || return 1
    with_retry crane tag "$dst" "${target##*:}" || return 1
    tags="\`$mirror/$target\`, \`$version\`"
  else
    src=$source
    dst="$mirror/$target"
    with_retry copy "$src" "$dst" || return 1
    tags="\`$dst\`"
  fi
  digest=$(with_retry crane digest "$dst") || return 1
  date=$(since "\`$mirror/$target\`" "$digest")
  row="| \`$src\` | $tags | \`$digest\` | ${date:-$today} |"
}

rows=()
failed=0
while read -r source target repo extra; do
  case "$source" in "" | "#"*) continue ;; esac
  if ! [[ "$source" =~ $ref && "$target" =~ ^[a-z0-9][a-z0-9._-]*:[A-Za-z0-9._-]+$ && -z "$extra" ]] ||
    { [ -n "$repo" ] && ! [[ "$repo" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; }; then
    echo "::error title=Mirror::invalid line: $source $target $repo $extra"
    failed=1
    continue
  fi
  echo "::group::$source -> $mirror/$target"
  row=""
  if mirror_one "$source" "$target" "$repo"; then
    rows+=("$row")
  else
    echo "::error title=Mirror::$source not mirrored after $attempts attempts"
    failed=1
    previous=$([ -f "$out" ] && grep -F "| \`$mirror/$target\`" "$out" || true)
    if [ -n "$previous" ]; then rows+=("$previous"); fi
  fi
  echo "::endgroup::"
done <<< "$IMAGES"

{
  echo "# Mirrored images"
  echo
  echo "Copies of the images used by Kanboto's CI kits and starters, so that CI does not depend on upstream"
  echo "registries' rate limits (Docker Hub's anonymous pulls in particular). Refreshed nightly by"
  echo "[\`mirror-images.yml\`](.github/workflows/mirror-images.yml): tools at their latest stable release"
  echo "(tag \`stable\`, plus the version tag), versioned images under their upstream tag. Manifests are copied"
  echo "intact, so each digest is the upstream one. Since: the date this digest was first mirrored."
  echo
  echo "| Source | Mirror | Digest | Since |"
  echo "|---|---|---|---|"
  if [ ${#rows[@]} -gt 0 ]; then printf '%s\n' "${rows[@]}"; fi
} > "$out"

exit "$failed"
