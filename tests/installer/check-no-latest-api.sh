#!/usr/bin/env bash
# =====================================================================
# check-no-latest-api.sh — static guard test.
#
# Asserts the property from spec/14-update/25-release-pinned-installer.md:
#   release-install.sh and release-install.ps1 MUST NOT call the GitHub
#   "releases/latest" API (or any api.github.com endpoint that resolves
#   "latest"). Comments and help text mentioning "/releases/latest" are
#   permitted; *executable* references are not.
#
# Strategy:
#   Flag a line ONLY when it both (a) invokes a network client
#   (curl, wget, Invoke-RestMethod, Invoke-WebRequest, irm, iwr) AND
#   (b) references `releases/latest` or `api.github.com` on the same
#   line. This permits help text, comments, and heredoc descriptions to
#   mention the forbidden endpoints — they are documenting the
#   prohibition.
#
# Exit: 0 clean, 1 violation found.
# =====================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SH="$REPO_ROOT/release-install.sh"
PS="$REPO_ROOT/release-install.ps1"
RC=0

CLIENT_RE='(curl|wget|Invoke-RestMethod|Invoke-WebRequest|\birm\b|\biwr\b)'
TARGET_RE='(releases/latest|api\.github\.com)'

check_file() {
  local file="$1" hits
  hits="$(grep -nE "$CLIENT_RE" "$file" | grep -E "$TARGET_RE" || true)"
  if [[ -n "$hits" ]]; then
    printf '  ❌ %s: network client invokes releases/latest or api.github.com\n' "$file" >&2
    printf '%s\n' "$hits" | sed 's/^/      /' >&2
    RC=1
  else
    printf '  ✅ %s: no executable call to releases/latest\n' "$file"
  fi
}

printf '\nT3: release-install.* MUST NOT call api.github.com/.../releases/latest\n'
[[ -f "$SH" ]] || { printf '  ❌ missing %s\n' "$SH" >&2; exit 1; }
[[ -f "$PS" ]] || { printf '  ❌ missing %s\n' "$PS" >&2; exit 1; }
check_file "$SH"
check_file "$PS"

exit $RC
