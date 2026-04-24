#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# install.sh — Download spec/linters/scripts from a GitHub repo
#
# Quick start (defaults from install-config.json):
#   ./install.sh
#   curl -fsSL https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v17/main/install.sh | bash
#
# Power-user flags:
# Power-user flags:
#   --repo owner/repo            Override source repo
#   --branch main                Override branch (ignored if --version given)
#   --version vX.Y.Z             Install a specific release tag
#   --folders spec,linters       Comma-separated folder list (subpaths OK: spec/14-update)
#   --dest /path/to/dir          Install destination (default: cwd)
#   --config my-config.json      Use custom config file
#   --prompt                     Ask before overwriting each existing file (y/n/a/s)
#   --force                      Overwrite all existing files without prompting
#   --dry-run                    Show what would change; write nothing
#   --list-versions              List available release tags and exit
#   --list-folders               List available top-level folders for the chosen ref and exit
#   -n | --no-latest             Skip the latest-version probe (use this installer as-is)
#                                (alias: --no-probe)
#   -h | --help                  Show this help
# ──────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────
CONFIG_FILE="install-config.json"
REPO=""
BRANCH=""
VERSION=""
DEST=""
FOLDERS=()
PROMPT_MODE=false
FORCE=false
DRY_RUN=false
LIST_VERSIONS=false
LIST_FOLDERS=false
PINNED_BY_RELEASE_INSTALL=""

# ── Colors ────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
DIM='\033[2m'
NC='\033[0m'

step()  { echo -e "${CYAN}▸ $1${NC}"; }
ok()    { echo -e "${GREEN}✅ $1${NC}"; }
warn()  { echo -e "${YELLOW}⚠️  $1${NC}"; }
err()   { echo -e "${RED}❌ $1${NC}" >&2; }
dim()   { echo -e "${DIM}$1${NC}"; }

usage() {
  sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

# ── Latest-version probe (unchanged) ──────────────────────────────
PROBE_OWNER_FALLBACK="alimtvnetwork"
PROBE_BASE_FALLBACK="coding-guidelines"
PROBE_VERSION_FALLBACK=14

invoke_latest_version_probe() {
    step "Detecting installer identity..."
    local src_url="${INSTALL_PROBE_SOURCE_URL:-${BASH_SOURCE[0]:-$0}}"
    local owner="${INSTALL_PROBE_OWNER:-}"
    local base="${INSTALL_PROBE_BASE:-}"
    local cur="${INSTALL_PROBE_VERSION:-}"
    local re='^https?://[^/]+/([^/]+)/([A-Za-z0-9._-]+)-v([0-9]+)/[^/]+/install\.sh'
    if [[ "$src_url" =~ $re ]]; then
        : "${owner:=${BASH_REMATCH[1]}}"
        : "${base:=${BASH_REMATCH[2]}}"
        : "${cur:=${BASH_REMATCH[3]}}"
    fi
    : "${owner:=$PROBE_OWNER_FALLBACK}"
    : "${base:=$PROBE_BASE_FALLBACK}"
    : "${cur:=$PROBE_VERSION_FALLBACK}"
    local current=$cur
    ok "Identity: $owner/$base-v$current  (probing v$((current+1))..v$((current+20)))"
    local depth=${INSTALL_PROBE_HANDOFF_DEPTH:-0}
    if [[ $depth -ge 3 ]]; then err "Probe loop guard (depth=$depth)"; exit 1; fi
    if ! command -v curl &>/dev/null; then warn "curl not found — skipping probe."; return 0; fi
    step "Probing 20 candidate versions in parallel (timeout 2s, middle-out)..."
    local tmp; tmp=$(mktemp -d)
    # Middle-out ordering: probe the middle of the range first, then expand
    # outward. With true parallelism this is correctness-equivalent, but it
    # plays better with any future early-abort logic (most active forks tend
    # to land mid-window of +1..+20).
    local low=$((current + 1))
    local high=$((current + 20))
    local mid=$(( (low + high) / 2 ))
    local order=("$mid")
    local offset upper lower
    for offset in $(seq 1 $((high - low))); do
        upper=$((mid + offset)); lower=$((mid - offset))
        [[ $upper -le $high ]] && order+=("$upper")
        [[ $lower -ge $low  ]] && order+=("$lower")
    done
    local n
    for n in "${order[@]}"; do
        (
            local url="https://raw.githubusercontent.com/$owner/$base-v$n/main/install.sh"
            local code; code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 -I "$url" 2>/dev/null || echo 000)
            if [[ "$code" == "200" || "$code" == "301" || "$code" == "302" ]]; then echo "$n" > "$tmp/$n"; fi
        ) &
    done
    local waited=0
    while [[ $waited -lt 4 ]]; do sleep 1; waited=$((waited + 1)); [[ -z "$(jobs -rp)" ]] && break; done
    wait 2>/dev/null || true
    local latest=$current
    # Always pick the highest hit (sort -n | tail -1 → descending winner).
    if compgen -G "$tmp/*" >/dev/null 2>&1; then latest=$(basename "$(ls "$tmp" | sort -n | tail -1)"); fi
    rm -rf "$tmp"
    if [[ $latest -le $current ]]; then ok "Already on latest (v$current)."; return 0; fi
    local newer_url="https://raw.githubusercontent.com/$owner/$base-v$latest/main/install.sh"
    ok "Newer version found: v$latest. Handing off..."
    export INSTALL_PROBE_HANDOFF_DEPTH=$((depth + 1))
    export INSTALL_PROBE_SOURCE_URL="$newer_url"
    if curl -fsSL "$newer_url" | bash; then exit 0; else exit $?; fi
}

# Skip probe when user pinned a version, asked for a listing, or was
# launched by release-install.sh (handshake = --pinned-by-release-install).
should_skip_probe() {
  for arg in "$@"; do
    case "$arg" in
      --version|--list-versions|--list-folders|--no-probe|--no-latest|-n|--pinned-by-release-install) return 0 ;;
    esac
  done
  [[ -n "${INSTALL_NO_PROBE:-}" ]] && return 0
  return 1
}

if ! should_skip_probe "$@"; then
  invoke_latest_version_probe || warn "Version probe error — continuing."
fi

# ── Parse CLI args ────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)           REPO="$2";        shift 2 ;;
    --branch)         BRANCH="$2";      shift 2 ;;
    --version)        VERSION="$2";     shift 2 ;;
    --folders)        IFS=',' read -ra FOLDERS <<< "$2"; shift 2 ;;
    --dest)           DEST="$2";        shift 2 ;;
    --config)         CONFIG_FILE="$2"; shift 2 ;;
    --prompt)         PROMPT_MODE=true; shift ;;
    --force)          FORCE=true;       shift ;;
    --dry-run)        DRY_RUN=true;     shift ;;
    --list-versions)  LIST_VERSIONS=true; shift ;;
    --list-folders)   LIST_FOLDERS=true; shift ;;
    --no-probe|--no-latest|-n) shift ;;
    --pinned-by-release-install) PINNED_BY_RELEASE_INSTALL="$2"; shift 2 ;;
    -h|--help)        usage ;;
    *) err "Unknown option: $1"; exit 1 ;;
  esac
done

# Pinning handshake: when invoked by release-install.sh, the version
# arg MUST agree with the handshake value. Mismatch = exit 2 so the
# parent can detect version skew (per spec §Failure Modes).
if [[ -n "$PINNED_BY_RELEASE_INSTALL" ]]; then
  if [[ -z "$VERSION" ]]; then
    VERSION="$PINNED_BY_RELEASE_INSTALL"
  elif [[ "$VERSION" != "$PINNED_BY_RELEASE_INSTALL" ]]; then
    err "Pinning handshake mismatch: --version=$VERSION vs --pinned-by-release-install=$PINNED_BY_RELEASE_INSTALL"
    exit 2
  fi
  step "Pinned by release-install: $PINNED_BY_RELEASE_INSTALL (auto-update disabled)"
fi

if $PROMPT_MODE && $FORCE; then
  err "--prompt and --force are mutually exclusive"
  exit 1
fi

# ── Read config (only for repo/branch/folders defaults) ───────────
read_config() {
  local file="$1"
  [[ ! -f "$file" ]] && return 1
  local parser=""
  command -v python3 &>/dev/null && parser="python3"
  [[ -z "$parser" ]] && command -v node &>/dev/null && parser="node"
  if [[ -z "$parser" ]]; then err "Need python3 or node to parse $file"; exit 1; fi
  local result
  if [[ "$parser" == "python3" ]]; then
    result="$(python3 -c "import json; c=json.load(open('$file')); print(c.get('repo','')); print(c.get('branch','')); print('\n'.join(c.get('folders',[])))")"
  else
    result="$(node -e "const c=require('./$file'); console.log(c.repo||''); console.log(c.branch||''); (c.folders||[]).forEach(f=>console.log(f));")"
  fi
  local i=0
  while IFS= read -r line; do
    if [[ $i -eq 0 ]]; then [[ -z "$REPO" ]] && REPO="$line"
    elif [[ $i -eq 1 ]]; then [[ -z "$BRANCH" ]] && BRANCH="$line"
    else [[ ${#FOLDERS[@]} -eq 0 ]] && FOLDERS+=("$line")
    fi
    ((i++))
  done <<< "$result"
}

if [[ -f "$CONFIG_FILE" ]]; then
  step "Reading config from $CONFIG_FILE"
  read_config "$CONFIG_FILE"
fi

REPO="${REPO:-alimtvnetwork/coding-guidelines-v17}"
BRANCH="${BRANCH:-main}"
DEST="${DEST:-$(pwd)}"
[[ ${#FOLDERS[@]} -eq 0 ]] && FOLDERS=("spec" "linters" "linter-scripts")

# Ref = tag if --version, else branch
REF="$BRANCH"
[[ -n "$VERSION" ]] && REF="$VERSION"

# ── Download helpers ──────────────────────────────────────────────
download_to_file() {
  local url="$1" output="$2"
  if command -v curl &>/dev/null; then curl -fsSL "$url" -o "$output"
  elif command -v wget &>/dev/null; then wget -qO "$output" "$url"
  else err "Neither curl nor wget found"; exit 1; fi
}

download_to_stdout() {
  local url="$1"
  if command -v curl &>/dev/null; then curl -fsSL "$url"
  elif command -v wget &>/dev/null; then wget -qO- "$url"
  else err "Neither curl nor wget found"; exit 1; fi
}

# ── Listing modes (exit early) ────────────────────────────────────
list_release_versions() {
  step "Fetching releases for $REPO..."
  local json; json="$(download_to_stdout "https://api.github.com/repos/$REPO/releases?per_page=50" 2>/dev/null || echo "")"
  if [[ -z "$json" ]]; then err "Could not fetch releases"; exit 1; fi
  echo ""
  echo "$json" | grep -o '"tag_name"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"tag_name"[[:space:]]*:[[:space:]]*"//;s/"$//' | head -50 | while read -r tag; do
    echo "  • $tag"
  done
  echo ""
  exit 0
}

list_top_folders() {
  step "Listing folders for $REPO@$REF..."
  local api="https://api.github.com/repos/$REPO/contents?ref=$REF"
  local json; json="$(download_to_stdout "$api" 2>/dev/null || echo "")"
  if [[ -z "$json" ]]; then err "Could not list folders"; exit 1; fi
  echo ""
  echo "$json" | python3 -c "
import json, sys
items = json.load(sys.stdin)
dirs = sorted([i['name'] for i in items if i.get('type') == 'dir'])
for d in dirs: print(f'  • {d}')
" 2>/dev/null || echo "$json" | grep -B1 '"type": *"dir"' | grep '"name"' | sed 's/.*"name"[[:space:]]*:[[:space:]]*"//;s/".*$//' | sed 's/^/  • /'
  echo ""
  exit 0
}

$LIST_VERSIONS && list_release_versions
$LIST_FOLDERS && list_top_folders

# ── Banner ────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════"
echo "  Spec & Scripts Installer"
echo "  Source:  $REPO @ $REF"
echo "  Folders: ${FOLDERS[*]}"
echo "  Dest:    $DEST"
$DRY_RUN     && echo "  Mode:    DRY-RUN (no writes)"
$PROMPT_MODE && echo "  Mode:    Interactive prompts (y/n/a/s)"
$FORCE       && echo "  Mode:    Force overwrite"
echo "════════════════════════════════════════════════════════"
echo ""

# ── Cleanup trap (with verification) ──────────────────────────────
TMP_DIR=""
cleanup() {
  [[ -z "${TMP_DIR:-}" ]] && return 0
  rm -rf "$TMP_DIR" 2>/dev/null || true
  if [[ ! -e "$TMP_DIR" ]]; then
    ok "Temp cleaned: $TMP_DIR"
  else
    warn "Temp NOT fully removed: $TMP_DIR (manual cleanup recommended)"
  fi
}
trap cleanup EXIT

# ── Fetch archive at REF (tarball, smaller) ───────────────────────
TMP_DIR="$(mktemp -d)"
ARCHIVE_PATH="$TMP_DIR/repo.tar.gz"
ARCHIVE_URL="https://codeload.github.com/$REPO/tar.gz/refs/heads/$BRANCH"
[[ -n "$VERSION" ]] && ARCHIVE_URL="https://codeload.github.com/$REPO/tar.gz/refs/tags/$VERSION"

step "Downloading $REPO@$REF..."
if ! download_to_file "$ARCHIVE_URL" "$ARCHIVE_PATH" 2>/dev/null; then
  # Fallback for tags that aren't refs/tags (some pipelines push as branch-like)
  ARCHIVE_URL="https://codeload.github.com/$REPO/tar.gz/$REF"
  download_to_file "$ARCHIVE_URL" "$ARCHIVE_PATH"
fi

step "Extracting..."
EXTRACT_DIR="$TMP_DIR/extracted"
mkdir -p "$EXTRACT_DIR"
tar -xzf "$ARCHIVE_PATH" -C "$EXTRACT_DIR"
ARCHIVE_ROOT="$(find "$EXTRACT_DIR" -mindepth 1 -maxdepth 1 -type d | head -1)"
[[ -z "$ARCHIVE_ROOT" ]] && { err "Failed to find archive root"; exit 1; }

# ── Merge with prompt/force/dry-run semantics ─────────────────────
PROMPT_ALL=false
PROMPT_SKIP_ALL=false
COPIED=0
SKIPPED_FILES=0
OVERWROTE=0
WROTE_NEW=0
SKIPPED_FOLDERS=0

decide_overwrite() {
  # Returns 0 to write, 1 to skip
  local target="$1"
  $PROMPT_ALL && return 0
  $PROMPT_SKIP_ALL && return 1
  $FORCE && return 0
  if ! $PROMPT_MODE; then return 0; fi  # default = overwrite (legacy behavior)
  while true; do
    echo -ne "${YELLOW}?${NC} Overwrite ${target#$DEST/} ? [y]es/[n]o/[a]ll/[s]kip-all: "
    read -r ans </dev/tty || ans="n"
    case "$ans" in
      y|Y) return 0 ;;
      n|N) return 1 ;;
      a|A) PROMPT_ALL=true; return 0 ;;
      s|S) PROMPT_SKIP_ALL=true; return 1 ;;
      *) echo "  enter y, n, a, or s" ;;
    esac
  done
}

merge_file() {
  local src="$1" target="$2"
  local target_dir; target_dir="$(dirname "$target")"
  if [[ -e "$target" ]]; then
    if decide_overwrite "$target"; then
      if $DRY_RUN; then dim "  ~ would overwrite ${target#$DEST/}"
      else mkdir -p "$target_dir"; cp -f "$src" "$target"; fi
      ((OVERWROTE++))
    else
      dim "  - skip ${target#$DEST/}"
      ((SKIPPED_FILES++))
    fi
  else
    if $DRY_RUN; then dim "  + would create ${target#$DEST/}"
    else mkdir -p "$target_dir"; cp -f "$src" "$target"; fi
    ((WROTE_NEW++))
  fi
}

merge_folder() {
  local folder="$1"
  local src="$ARCHIVE_ROOT/$folder"
  if [[ ! -d "$src" ]]; then
    warn "Folder '$folder' not found in $REPO@$REF — skipping"
    ((SKIPPED_FOLDERS++))
    return
  fi
  step "Merging: $folder"
  while IFS= read -r -d '' f; do
    local rel="${f#$src/}"
    merge_file "$f" "$DEST/$folder/$rel"
  done < <(find "$src" -type f -print0)
  ((COPIED++))
}

for folder in "${FOLDERS[@]}"; do
  merge_folder "$folder"
done

# ── Summary ───────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════"
[[ $COPIED -gt 0 ]] && ok "$COPIED folder(s) processed"
[[ $WROTE_NEW -gt 0 ]] && ok "$WROTE_NEW new file(s)"
[[ $OVERWROTE -gt 0 ]] && ok "$OVERWROTE file(s) overwritten"
[[ $SKIPPED_FILES -gt 0 ]] && warn "$SKIPPED_FILES file(s) skipped"
[[ $SKIPPED_FOLDERS -gt 0 ]] && warn "$SKIPPED_FOLDERS folder(s) missing in source"
$DRY_RUN && warn "DRY-RUN — no changes written"
echo ""
echo "  Source:      $REPO @ $REF"
echo "  Destination: $DEST"
echo "  Folders:     ${FOLDERS[*]}"
echo ""
echo "════════════════════════════════════════════════════════"
