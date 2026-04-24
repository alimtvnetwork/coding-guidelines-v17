#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# release-install.sh — Pinned-version installer for GitHub Releases
#
# This script is the release-page counterpart to install.sh. It NEVER
# resolves "latest". It installs exactly the version it was built for
# (baked at release time) or the version explicitly passed via
# --version.
#
# Spec: spec/14-update/25-release-pinned-installer.md
#
# Quick start:
#   curl -fsSL https://github.com/<owner>/<repo>/releases/download/vX.Y.Z/release-install.sh | bash
#   ./release-install.sh --version v3.21.0
#
# Flags:
#   --version vX.Y.Z   Install this exact tag (overrides baked-in value).
#   --no-update        No-op. Pinning is always on; flag accepted for
#                      ergonomics / muscle-memory parity.
#   -h | --help        Show this help.
#
# Exit codes (per spec §Failure Modes):
#   0  success
#   1  no version resolvable (no arg + no baked-in tag)
#   2  invalid version string (semver regex failed)
#   3  pinned release / asset not found (404)
#   4  verification failed (raised by the inner installer; see
#      spec/14-update/27-generic-installer-behavior.md §8)
#   5  inner installer rejected pinning handshake
# ──────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Build-time substitution target ────────────────────────────────
# The release workflow replaces the literal string `__VERSION_PLACEHOLDER__`
# with the concrete tag (e.g. v3.21.0) when uploading this file as a
# release asset. Unbaked checkouts keep the placeholder verbatim.
BAKED_VERSION="__VERSION_PLACEHOLDER__"

REPO="alimtvnetwork/coding-guidelines-v17"
SEMVER_RE='^v?[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9.]+)?$'

# ── Colors / output ───────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'
YELLOW='\033[1;33m'; DIM='\033[2m'; NC='\033[0m'
step() { echo -e "${CYAN}▸ $1${NC}"; }
ok()   { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}" >&2; }
err()  { echo -e "${RED}❌ $1${NC}" >&2; }

usage() {
  cat <<'HELP'
release-install.sh — pinned-version installer for GitHub Releases

USAGE
  release-install.sh [--version <tag>] [--no-update] [-h|--help]

MODE DISPATCH (spec §3)
  This installer ALWAYS runs in PINNED MODE. Per spec §4 it MUST install
  exactly the resolved tag and is forbidden from:
    • querying /releases/latest
    • falling back to the main branch
    • crossing repo boundaries (no V→V+N discovery)
    • picking a "compatible" or "nearest" version
    • silently downgrading to implicit mode

  IMPLICIT MODE is unreachable here by design — use install.sh / one of
  the bundle installers if you want implicit-latest behavior.

RESOLUTION ORDER (highest precedence first, spec §4.3)
  1. --version <tag>    (CLI flag)
  2. $INSTALLER_VERSION (env var, if set)
  3. __VERSION_PLACEHOLDER__ baked at release-asset build time
  If two sources disagree, a warning is emitted and the higher-precedence
  value wins.

FLAGS
  --version <tag>   [PINNED only — required if no baked tag]
                    Install exactly this tag. Overrides the baked-in
                    placeholder. Must match ^v?\\d+\\.\\d+\\.\\d+(-pre)?$.
  --no-update       No-op. Pinning is always on; flag is accepted for
                    parity with implicit installers.
  -h, --help        Show this help and exit.

EXIT CODES (spec §8 + release-install §4 details)
  0  success
  1  no version resolvable (no flag, no env, no baked tag)
  2  invalid version string (semver regex failed) / unknown flag
  3  pinned release / tag-tarball not found at either GitHub endpoint
  4  verification failed (raised by the inner installer)
  5  inner installer rejected the pinning handshake

SPEC
  spec/14-update/25-release-pinned-installer.md  (this script)
  spec/14-update/27-generic-installer-behavior.md (§3, §4, §7, §8)
HELP
  exit 0
}

# ── Argument parsing ──────────────────────────────────────────────
ARG_VERSION=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)   ARG_VERSION="$2"; shift 2 ;;
    --no-update) shift ;;
    -h|--help)   usage ;;
    *) err "Unknown option: $1"; exit 2 ;;
  esac
done

# ── Resolve pinned version (spec §Resolution Algorithm) ───────────
# Precedence (spec §B.2 + ratified env-var extension §B.2.b'):
#   1. --version flag
#   2. $INSTALLER_VERSION env var
#   3. Baked __VERSION_PLACEHOLDER__
resolve_version() {
  if [[ -n "$ARG_VERSION" ]]; then
    if [[ "$BAKED_VERSION" != "__VERSION_PLACEHOLDER__" \
          && "$BAKED_VERSION" != "$ARG_VERSION" ]]; then
      warn "Argument version ($ARG_VERSION) overrides baked-in ($BAKED_VERSION)."
    fi
    echo "$ARG_VERSION"
    return 0
  fi
  if [[ -n "${INSTALLER_VERSION:-}" ]]; then
    if [[ "$BAKED_VERSION" != "__VERSION_PLACEHOLDER__" \
          && "$BAKED_VERSION" != "$INSTALLER_VERSION" ]]; then
      warn "Env INSTALLER_VERSION ($INSTALLER_VERSION) overrides baked-in ($BAKED_VERSION)."
    fi
    echo "$INSTALLER_VERSION"
    return 0
  fi
  if [[ "$BAKED_VERSION" != "__VERSION_PLACEHOLDER__" ]]; then
    echo "$BAKED_VERSION"
    return 0
  fi
  return 1
}

if ! RESOLVED="$(resolve_version)"; then
  err "release-install requires a pinned version."
  err "Pass --version <tag> or run the baked copy from a Release page."
  exit 1
fi

# ── Validate (spec §Validation) ───────────────────────────────────
if ! [[ "$RESOLVED" =~ $SEMVER_RE ]]; then
  err "Invalid version format: '$RESOLVED'"
  err "Expected semver, e.g. v3.21.0 or 3.21.0-beta.1"
  exit 2
fi

ok "Installing pinned version: $RESOLVED"

# ── Spec §7 banner ───────────────────────────────────────────────
echo ""
echo "  📦 release-install (pinned)"
echo "     mode:    pinned"
echo "     repo:    $REPO"
echo "     version: $RESOLVED"
echo "     source:  release-asset"
echo ""

# ── HEAD-check pinned asset (spec §4.1 dual endpoint) ────────────
# §4.1 REQUIRES: try /releases/download/<tag>/ first, then the tag
# tarball /archive/refs/tags/<tag>. Both URLs are bound to the SAME
# pinned tag — this is NOT a §4.2 main-branch / cross-repo fallback.
PRIMARY_URL="https://github.com/$REPO/releases/download/$RESOLVED/source-code.tar.gz"
TAG_TARBALL_URL="https://codeload.github.com/$REPO/tar.gz/refs/tags/$RESOLVED"

probe_url() {
  local url="$1"
  curl -sIL -o /dev/null -w '%{http_code}' --max-time 5 "$url" 2>/dev/null || echo 000
}

step "Probing primary release asset..."
PRIMARY_CODE="$(probe_url "$PRIMARY_URL")"
DOWNLOAD_URL=""
if [[ "$PRIMARY_CODE" == "200" ]]; then
  DOWNLOAD_URL="$PRIMARY_URL"
  ok "Found release asset: $PRIMARY_URL"
else
  warn "Primary asset returned HTTP $PRIMARY_CODE — trying tag tarball (still pinned to $RESOLVED)."
  TAG_CODE="$(probe_url "$TAG_TARBALL_URL")"
  if [[ "$TAG_CODE" == "200" ]]; then
    DOWNLOAD_URL="$TAG_TARBALL_URL"
    ok "Found tag tarball: $TAG_TARBALL_URL"
  else
    err "Release '$RESOLVED' not found at either location:"
    err "  primary:  $PRIMARY_URL  (HTTP $PRIMARY_CODE)"
    err "  tag tarball: $TAG_TARBALL_URL (HTTP $TAG_CODE)"
    err "Verify the tag exists at https://github.com/$REPO/releases"
    err "Per spec §4.2, this installer will NOT fall back to main or other tags."
    exit 3
  fi
fi

# ── Hand off to inner installer with pinning handshake ────────────
INSTALL_URL="https://raw.githubusercontent.com/$REPO/$RESOLVED/install.sh"
step "Handing off to inner installer (pinned)..."
echo -e "${DIM}  Source: $INSTALL_URL${NC}"
echo -e "${DIM}  Pinned: $RESOLVED${NC}"

if ! command -v curl &>/dev/null; then
  err "curl is required for hand-off"
  exit 1
fi

set +e
curl -fsSL "$INSTALL_URL" | bash -s -- \
  --pinned-by-release-install "$RESOLVED" \
  --version "$RESOLVED" \
  --no-latest
HANDOFF_EXIT=$?
set -e

if [[ $HANDOFF_EXIT -ne 0 ]]; then
  err "Inner installer exited with code $HANDOFF_EXIT"
  if [[ $HANDOFF_EXIT -eq 2 ]]; then
    err "Pinning handshake may have been rejected (version skew?)"
    exit 5
  fi
  exit "$HANDOFF_EXIT"
fi

ok "Pinned install complete: $RESOLVED"
