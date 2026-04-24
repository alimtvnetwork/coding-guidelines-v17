#!/usr/bin/env bash
# =====================================================================
# check-release-bake.sh — bake-output integration test.
#
# Runs ./release.sh end-to-end and asserts:
#   1. release-artifacts/release-install.sh    exists
#   2. release-artifacts/release-install.ps1   exists
#   3. Neither baked file still contains __VERSION_PLACEHOLDER__
#   4. Both baked files carry the resolved tag (vX.Y.Z from package.json)
#   5. checksums.txt lists both baked installers
#
# Spec: spec/14-update/25-release-pinned-installer.md §Release-Time
#       Build Step (Job Sequence Job 2.b).
#
# Exit: 0 all pass, 1 any fail.
# =====================================================================
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RC=0

assert() {
  local name="$1" cond="$2"
  if eval "$cond" >/dev/null 2>&1; then
    printf '  ✅ %s\n' "$name"
  else
    printf '  ❌ %s   (failed: %s)\n' "$name" "$cond" >&2
    RC=1
  fi
}

printf '\nT5: release.sh bake-output integration\n'

cd "$REPO_ROOT"
TAG="v$(sed -nE 's/^[[:space:]]*"version":[[:space:]]*"([^"]+)".*$/\1/p' package.json | head -n1)"

if ! bash release.sh >/tmp/release.log 2>&1; then
  printf '  ❌ release.sh failed\n' >&2
  tail -20 /tmp/release.log >&2
  exit 1
fi

DIR="$REPO_ROOT/release-artifacts"
SH="$DIR/release-install.sh"
PS1="$DIR/release-install.ps1"
SUMS="$DIR/checksums.txt"

assert "baked release-install.sh exists"        "[[ -f '$SH' ]]"
assert "baked release-install.ps1 exists"       "[[ -f '$PS1' ]]"
assert "no placeholder remains in .sh"          "! grep -q __VERSION_PLACEHOLDER__ '$SH'"
assert "no placeholder remains in .ps1"         "! grep -q __VERSION_PLACEHOLDER__ '$PS1'"
assert ".sh has BAKED_VERSION=\"$TAG\""         "grep -qF 'BAKED_VERSION=\"$TAG\"' '$SH'"
assert ".ps1 has BakedVersion = \"$TAG\""       "grep -qF 'BakedVersion = \"$TAG\"' '$PS1'"
assert "checksums lists release-install.sh"     "grep -q 'release-install.sh' '$SUMS'"
assert "checksums lists release-install.ps1"    "grep -q 'release-install.ps1' '$SUMS'"

exit $RC
