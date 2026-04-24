#!/usr/bin/env bash
set -euo pipefail

REPO="alimtvnetwork/coding-guidelines-v17"
RELEASE_VERSION_INPUT="${RELEASE_VERSION:-}"
REQUIRED_PATHS=("spec" "linters" "linter-scripts" "install.sh" "install.ps1" "install-config.json" "readme.md" "release-install.sh" "release-install.ps1")

step() { printf '\033[0;36m▸ %s\033[0m\n' "$1"; }
ok() { printf '\033[0;32m✅ %s\033[0m\n' "$1"; }
err() { printf '\033[0;31m❌ %s\033[0m\n' "$1" >&2; }

resolve_version() {
  local version="${RELEASE_VERSION_INPUT#v}"

  if [[ -n "$version" ]]; then
    printf '%s\n' "$version"
    return 0
  fi

  version="$(sed -nE 's/^[[:space:]]*"version":[[:space:]]*"([^"]+)".*$/\1/p' package.json | head -n 1)"
  if [[ -n "$version" ]]; then
    printf '%s\n' "$version"
    return 0
  fi

  err "Unable to resolve version from RELEASE_VERSION or package.json"
  exit 1
}

VERSION="$(resolve_version)"
DIST_DIR="release-artifacts"
STAGING_DIR="$DIST_DIR/coding-guidelines-v$VERSION"
ARCHIVE_BASENAME="coding-guidelines-v$VERSION"

ensure_required_paths() {
  local is_missing=false

  for path in "${REQUIRED_PATHS[@]}"; do
    if [[ -e "$path" ]]; then
      continue
    fi

    err "Missing required path: $path"
    is_missing=true
  done

  if [[ "$is_missing" == true ]]; then
    exit 1
  fi
}

prepare_staging_dir() {
  rm -rf "$STAGING_DIR"
  mkdir -p "$STAGING_DIR"
}

copy_release_files() {
  cp -R spec "$STAGING_DIR/spec"
  cp -R linters "$STAGING_DIR/linters"
  cp -R linter-scripts "$STAGING_DIR/linter-scripts"
  cp install.sh "$STAGING_DIR/install.sh"
  cp install.ps1 "$STAGING_DIR/install.ps1"
  cp install-config.json "$STAGING_DIR/install-config.json"
  cp readme.md "$STAGING_DIR/readme.md"
}

create_archives() {
  local zip_path="$DIST_DIR/$ARCHIVE_BASENAME.zip"
  local tar_path="$DIST_DIR/$ARCHIVE_BASENAME.tar.gz"

  rm -f "$zip_path" "$tar_path"
  (cd "$DIST_DIR" && zip -qr "$ARCHIVE_BASENAME.zip" "$ARCHIVE_BASENAME")
  tar -C "$DIST_DIR" -czf "$tar_path" "$ARCHIVE_BASENAME"
}

bake_release_installers() {
  # Spec: spec/14-update/25-release-pinned-installer.md §Release-Time Build Step
  # Take the canonical release-install.{sh,ps1} from repo root, substitute
  # __VERSION_PLACEHOLDER__ with the resolved tag (prefixed with `v`), and
  # write standalone copies to $DIST_DIR for upload as release assets.
  local tag="v$VERSION"
  local out_sh="$DIST_DIR/release-install.sh"
  local out_ps1="$DIST_DIR/release-install.ps1"

  if [[ ! -f release-install.sh || ! -f release-install.ps1 ]]; then
    err "Canonical release-install scripts missing at repo root"
    exit 1
  fi

  sed "s/__VERSION_PLACEHOLDER__/$tag/g" release-install.sh  > "$out_sh"
  sed "s/__VERSION_PLACEHOLDER__/$tag/g" release-install.ps1 > "$out_ps1"
  chmod +x "$out_sh"

  if grep -q '__VERSION_PLACEHOLDER__' "$out_sh" "$out_ps1"; then
    err "Baking failed — placeholder still present in baked installers"
    exit 1
  fi
  if ! grep -q "BAKED_VERSION=\"$tag\""    "$out_sh";  then err "release-install.sh did not bake to $tag";  exit 1; fi
  if ! grep -q "BakedVersion = \"$tag\""   "$out_ps1"; then err "release-install.ps1 did not bake to $tag"; exit 1; fi
}

generate_checksums() {
  (cd "$DIST_DIR" && sha256sum \
    "$ARCHIVE_BASENAME.zip" \
    "$ARCHIVE_BASENAME.tar.gz" \
    "release-install.sh" \
    "release-install.ps1" \
    > checksums.txt)
}

print_summary() {
  cat <<EOF

════════════════════════════════════════════════════════
  Coding Guidelines Release Pack
  Version:     v$VERSION
  Repo:        $REPO
  Output:      $DIST_DIR
  Raw PS URL:  https://raw.githubusercontent.com/$REPO/main/install.ps1
  Raw SH URL:  https://raw.githubusercontent.com/$REPO/main/install.sh
════════════════════════════════════════════════════════

  Pinned one-liners (paste into the GitHub Release body):

  PowerShell:
    irm https://github.com/$REPO/releases/download/v$VERSION/release-install.ps1 | iex

  Bash:
    curl -fsSL https://github.com/$REPO/releases/download/v$VERSION/release-install.sh | bash

  Upload these assets to the v$VERSION release:
    - $ARCHIVE_BASENAME.zip
    - $ARCHIVE_BASENAME.tar.gz
    - release-install.sh         (baked, pinned to v$VERSION)
    - release-install.ps1        (baked, pinned to v$VERSION)
    - checksums.txt
EOF
}

step "Validating required files"
ensure_required_paths
step "Preparing release staging directory"
prepare_staging_dir
step "Copying release files"
copy_release_files
step "Creating archives"
create_archives
step "Baking release-install.{sh,ps1} with VERSION_PLACEHOLDER → v$VERSION"
bake_release_installers
step "Generating checksums"
generate_checksums
ok "Release artifacts created"
print_summary
