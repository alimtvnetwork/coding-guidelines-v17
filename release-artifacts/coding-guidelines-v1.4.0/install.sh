#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# install.sh — Download specific folders from a GitHub repo
#
# Usage:
#   ./install.sh                           # use install-config.json defaults
#   ./install.sh --repo owner/repo         # override source repo
#   ./install.sh --branch dev              # override branch
#   ./install.sh --config my-config.json   # use custom config file
#   curl -fsSL https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v17/main/install.sh | bash
# ──────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────
CONFIG_FILE="install-config.json"
REPO=""
BRANCH=""
FOLDERS=()

# ── Colors ────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

step()  { echo -e "${CYAN}▸ $1${NC}"; }
ok()    { echo -e "${GREEN}✅ $1${NC}"; }
warn()  { echo -e "${YELLOW}⚠️  $1${NC}"; }
err()   { echo -e "${RED}❌ $1${NC}" >&2; }

# ── Parse CLI args ────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)    REPO="$2";        shift 2 ;;
    --branch)  BRANCH="$2";      shift 2 ;;
    --config)  CONFIG_FILE="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--repo owner/repo] [--branch main] [--config file.json]"
      exit 0
      ;;
    *) err "Unknown option: $1"; exit 1 ;;
  esac
done

# ── Read config ───────────────────────────────────────────────────
read_config() {
  local file="$1"

  if [[ ! -f "$file" ]]; then
    return 1
  fi

  if command -v python3 &>/dev/null; then
    _parse_with_python "$file"
    return 0
  fi

  if command -v node &>/dev/null; then
    _parse_with_node "$file"
    return 0
  fi

  err "No JSON parser found (need python3 or node)"
  exit 1
}

_parse_with_python() {
  local file="$1"
  local result
  result="$(python3 -c "
import json, sys
with open('$file') as f:
    cfg = json.load(f)
print(cfg.get('repo', ''))
print(cfg.get('branch', ''))
print('\n'.join(cfg.get('folders', [])))
")"

  local i=0
  while IFS= read -r line; do
    if [[ $i -eq 0 ]]; then
      [[ -z "$REPO" ]] && REPO="$line"
    elif [[ $i -eq 1 ]]; then
      [[ -z "$BRANCH" ]] && BRANCH="$line"
    else
      FOLDERS+=("$line")
    fi
    ((i++))
  done <<< "$result"
}

_parse_with_node() {
  local file="$1"
  local result
  result="$(node -e "
const cfg = require('./$file');
console.log(cfg.repo || '');
console.log(cfg.branch || '');
(cfg.folders || []).forEach(f => console.log(f));
")"

  local i=0
  while IFS= read -r line; do
    if [[ $i -eq 0 ]]; then
      [[ -z "$REPO" ]] && REPO="$line"
    elif [[ $i -eq 1 ]]; then
      [[ -z "$BRANCH" ]] && BRANCH="$line"
    else
      FOLDERS+=("$line")
    fi
    ((i++))
  done <<< "$result"
}

# ── Load config ───────────────────────────────────────────────────
if [[ -f "$CONFIG_FILE" ]]; then
  step "Reading config from $CONFIG_FILE"
  read_config "$CONFIG_FILE"
else
  warn "No config file found at $CONFIG_FILE — using defaults"
fi

# Apply fallback defaults
REPO="${REPO:-alimtvnetwork/coding-guidelines-v17}"
BRANCH="${BRANCH:-main}"

if [[ ${#FOLDERS[@]} -eq 0 ]]; then
  FOLDERS=("spec" "linters" "linter-scripts")
fi

# ── Banner ────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════"
echo "  Spec & Scripts Installer"
echo "  Source:  $REPO (branch: $BRANCH)"
echo "  Folders: ${FOLDERS[*]}"
echo "════════════════════════════════════════════════════════"
echo ""

# ── Download function ─────────────────────────────────────────────
download() {
  local url="$1"
  local output="$2"

  if command -v curl &>/dev/null; then
    curl -fsSL "$url" -o "$output"
  elif command -v wget &>/dev/null; then
    wget -qO "$output" "$url"
  else
    err "Neither curl nor wget found"
    exit 1
  fi
}

# ── Cleanup trap ──────────────────────────────────────────────────
TMP_DIR=""
cleanup() {
  [[ -n "${TMP_DIR:-}" ]] && rm -rf "$TMP_DIR"
}
trap cleanup EXIT

# ── Step 1: Check for GitHub release ──────────────────────────────
step "Checking for GitHub releases..."

RELEASE_ARCHIVE=""
RELEASE_URL="https://api.github.com/repos/$REPO/releases/latest"

if command -v curl &>/dev/null; then
  RELEASE_JSON="$(curl -fsSL "$RELEASE_URL" 2>/dev/null || echo "")"
elif command -v wget &>/dev/null; then
  RELEASE_JSON="$(wget -qO- "$RELEASE_URL" 2>/dev/null || echo "")"
else
  RELEASE_JSON=""
fi

if [[ -n "$RELEASE_JSON" ]] && echo "$RELEASE_JSON" | grep -q '"zipball_url"'; then
  ok "Release found — downloading release archive"
  RELEASE_ARCHIVE="$(echo "$RELEASE_JSON" | grep -o '"zipball_url"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"zipball_url"[[:space:]]*:[[:space:]]*"//' | sed 's/"$//')"
fi

# ── Step 2: Download archive ─────────────────────────────────────
TMP_DIR="$(mktemp -d)"
ARCHIVE_PATH="$TMP_DIR/repo.zip"

if [[ -n "$RELEASE_ARCHIVE" ]]; then
  step "Downloading release archive..."
  download "$RELEASE_ARCHIVE" "$ARCHIVE_PATH"
else
  step "No release found — downloading branch archive..."
  ARCHIVE_URL="https://github.com/$REPO/archive/refs/heads/$BRANCH.zip"
  download "$ARCHIVE_URL" "$ARCHIVE_PATH"
fi

# ── Step 3: Extract archive ───────────────────────────────────────
step "Extracting archive..."
EXTRACT_DIR="$TMP_DIR/extracted"
mkdir -p "$EXTRACT_DIR"

if command -v unzip &>/dev/null; then
  unzip -qo "$ARCHIVE_PATH" -d "$EXTRACT_DIR"
else
  # Fallback: python3 zipfile
  python3 -c "
import zipfile, sys
with zipfile.ZipFile('$ARCHIVE_PATH', 'r') as z:
    z.extractall('$EXTRACT_DIR')
"
fi

# Find the root directory inside the archive (GitHub adds a prefix)
ARCHIVE_ROOT="$(find "$EXTRACT_DIR" -mindepth 1 -maxdepth 1 -type d | head -1)"

if [[ -z "$ARCHIVE_ROOT" ]]; then
  err "Failed to find extracted archive root"
  exit 1
fi

# ── Step 4: Copy folders ─────────────────────────────────────────
DEST_DIR="$(pwd)"
COPIED=0
SKIPPED=0

for folder in "${FOLDERS[@]}"; do
  SRC="$ARCHIVE_ROOT/$folder"

  if [[ ! -d "$SRC" ]]; then
    warn "Folder '$folder' not found in source repo — skipping"
    ((SKIPPED++))
    continue
  fi

  step "Merging folder: $folder"
  # Use cp with merge semantics (no --remove-destination)
  # -r: recursive, -f: force overwrite existing files
  cp -rf "$SRC/." "$DEST_DIR/$folder/"
  ok "Merged $folder"
  ((COPIED++))
done

# ── Summary ───────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════"

if [[ $COPIED -gt 0 ]]; then
  ok "$COPIED folder(s) installed successfully"
fi

if [[ $SKIPPED -gt 0 ]]; then
  warn "$SKIPPED folder(s) not found in source"
fi

echo ""
echo "  Source:      $REPO ($BRANCH)"
echo "  Destination: $DEST_DIR"
echo "  Folders:     ${FOLDERS[*]}"
echo ""
echo "════════════════════════════════════════════════════════"
