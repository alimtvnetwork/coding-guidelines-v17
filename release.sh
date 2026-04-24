#!/usr/bin/env bash
set -euo pipefail

REPO="alimtvnetwork/coding-guidelines-v15"
RELEASE_VERSION_INPUT="${RELEASE_VERSION:-}"
REQUIRED_PATHS=("spec" "linters" "linter-scripts" "install.sh" "install.ps1" "install-config.json" "README.md")

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
  cp README.md "$STAGING_DIR/README.md"
}

create_archives() {
  local zip_path="$DIST_DIR/$ARCHIVE_BASENAME.zip"
  local tar_path="$DIST_DIR/$ARCHIVE_BASENAME.tar.gz"

  rm -f "$zip_path" "$tar_path"
  (cd "$DIST_DIR" && zip -qr "$ARCHIVE_BASENAME.zip" "$ARCHIVE_BASENAME")
  tar -C "$DIST_DIR" -czf "$tar_path" "$ARCHIVE_BASENAME"
}

generate_checksums() {
  (cd "$DIST_DIR" && sha256sum "$ARCHIVE_BASENAME.zip" "$ARCHIVE_BASENAME.tar.gz" > checksums.txt)
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
step "Generating checksums"
generate_checksums
ok "Release artifacts created"
print_summary
