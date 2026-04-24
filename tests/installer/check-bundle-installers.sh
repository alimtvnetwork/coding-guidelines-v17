#!/usr/bin/env bash
# =====================================================================
# check-bundle-installers.sh — generated bundle installers conformance.
#
# For every bundle declared in bundles.json, asserts that the matching
# pair {<name>-install.sh, <name>-install.ps1} exist at the repo root
# and conform to spec/14-update/27-generic-installer-behavior.md:
#
#   STRUCTURAL (spec §3, §7, §8):
#     - bash:  usage(), --version, --no-discovery, --no-main-fallback,
#              --use-local-archive, -h|--help, "EXIT CODES (spec §8)",
#              "mode:    " banner field, spec §27 cross-ref
#     - ps1:   -Version, -NoDiscovery, -NoMainFallback, -UseLocalArchive,
#              -Help (with comment-based-help bridge), "EXIT CODES",
#              "mode:    " banner field, spec §27 cross-ref
#
#   STATIC SAFETY:
#     - bash -n parses cleanly
#     - no line both invokes a network client AND references
#       releases/latest or api.github.com
#
# Exit: 0 all pass, 1 any fail.
# =====================================================================
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RC=0
PASS=0
FAIL=0

require() {
  local file="$1" needle="$2" label="$3"
  if grep -qF -- "$needle" "$file"; then
    PASS=$((PASS+1))
  else
    printf '    ❌ %s: missing %s\n' "$label" "$needle" >&2
    FAIL=$((FAIL+1))
    RC=1
  fi
}

check_sh() {
  local file="$1"
  if ! bash -n "$file" 2>/dev/null; then
    printf '    ❌ %s: bash -n failed\n' "$(basename "$file")" >&2
    RC=1
    return
  fi
  for needle in 'usage()' '--version' '--no-discovery' '--no-main-fallback' \
                '--use-local-archive' '-h|--help' 'EXIT CODES (spec §8)' \
                'mode:    ' 'spec/14-update/27-generic-installer-behavior'; do
    require "$file" "$needle" "$(basename "$file")"
  done
}

check_ps1() {
  local file="$1"
  for needle in '-Version' '-NoDiscovery' '-NoMainFallback' \
                '-UseLocalArchive' '[switch]$Help' 'Get-Help $PSCommandPath' \
                'EXIT CODES' 'mode:    ' \
                'spec/14-update/27-generic-installer-behavior'; do
    require "$file" "$needle" "$(basename "$file")"
  done
}

check_no_latest() {
  local file="$1"
  local hits
  hits="$(grep -nE '(curl|wget|Invoke-RestMethod|Invoke-WebRequest|\birm\b|\biwr\b)' "$file" \
          | grep -E '(releases/latest|api\.github\.com)' || true)"
  if [[ -n "$hits" ]]; then
    printf '    ❌ %s: forbidden network call\n%s\n' "$(basename "$file")" "$hits" >&2
    RC=1
  fi
}

printf '\nT6: bundle installer conformance (14 files = 7 bundles × 2 platforms)\n'

cd "$REPO_ROOT"
BUNDLES="$(node -e 'const m=require("./bundles.json");console.log(m.bundles.map(b=>b.name).join(" "))')"

for name in $BUNDLES; do
  sh_file="$REPO_ROOT/$name-install.sh"
  ps_file="$REPO_ROOT/$name-install.ps1"
  if [[ ! -f "$sh_file" || ! -f "$ps_file" ]]; then
    printf '  ❌ %-20s missing installer pair\n' "$name" >&2
    RC=1
    continue
  fi
  printf '  • %s\n' "$name"
  check_sh       "$sh_file"
  check_no_latest "$sh_file"
  check_ps1      "$ps_file"
  check_no_latest "$ps_file"
done

printf '\n  → %d structural assertions passed, %d failed\n' "$PASS" "$FAIL"
exit $RC
