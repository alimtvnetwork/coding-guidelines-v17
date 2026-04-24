#!/usr/bin/env bash
# =====================================================================
# check-release-install-acceptance.sh — exit-code acceptance tests.
#
# Validates spec/14-update/25-release-pinned-installer.md §F (Failure
# Modes) and §AC (Acceptance Criteria) for release-install.sh:
#
#   AC.1 → exit 1 when no version is resolvable
#   AC.5 → exit 2 when tag fails semver regex (BEFORE any network call)
#   B.2.b → $INSTALLER_VERSION env var is honored as precedence-2
#
# These are static behaviors — no real download is attempted; the env-var
# path is satisfied as soon as it prints "Installing pinned version".
#
# Exit: 0 all pass, 1 any fail.
# =====================================================================
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SH="$REPO_ROOT/release-install.sh"
RC=0

assert_exit() {
  local name="$1" expected="$2" actual="$3"
  if [[ "$actual" == "$expected" ]]; then
    printf '  ✅ %s → exit %s\n' "$name" "$actual"
  else
    printf '  ❌ %s → expected exit %s, got %s\n' "$name" "$expected" "$actual" >&2
    RC=1
  fi
}

printf '\nT4: release-install.sh exit-code acceptance\n'

# AC.1 — no version, no env, no baked → exit 1
bash "$SH" >/dev/null 2>&1
assert_exit "no version resolvable" 1 $?

# AC.5 — invalid semver → exit 2 (before network)
bash "$SH" --version "main" >/dev/null 2>&1
assert_exit "invalid semver 'main'"   2 $?
bash "$SH" --version "v1.2"  >/dev/null 2>&1
assert_exit "invalid semver 'v1.2'"   2 $?
bash "$SH" --version ""      >/dev/null 2>&1
assert_exit "empty --version"         1 $?

# B.2.b — env-var path: must accept and reach the probe step (exit 3 on
# unreachable v9.99.99 asset). We only care it gets PAST validation.
output="$(INSTALLER_VERSION=v9.99.99 bash "$SH" 2>&1 || true)"
if grep -q "Installing pinned version: v9.99.99" <<<"$output"; then
  printf '  ✅ $INSTALLER_VERSION honored as precedence-2\n'
else
  printf '  ❌ $INSTALLER_VERSION not honored\n' >&2
  printf '%s\n' "$output" | sed 's/^/      /' >&2
  RC=1
fi

exit $RC
