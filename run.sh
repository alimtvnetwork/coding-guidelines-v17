#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# run.sh — root convenience runner with sub-commands
#
# Sub-commands (first positional arg):
#   (none)   → lint  (legacy default — git pull + Go validator on src/)
#   lint     → same as no-args, but explicit
#   slides   → git pull → build slides-app/ → preview → open in browser
#   help     → print this table
#
# Spec: spec/15-distribution-and-runner/02-runner-contract.md
# ──────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

show_help() {
  cat <<'EOF'

  coding-guidelines-v17 — root runner

  Usage: ./run.sh [<command>] [<flags>]

  Commands:
    (none)   git pull + run Go validator on src/   (legacy default)
    lint     same as no-args, but explicit
    slides   build & preview slides-app/, open browser
    help     this table

  Lint flags forwarded to linter-scripts/run.sh:
    --path <dir>      Directory to scan (default: src)
    --max-lines <n>   Max function body lines (default: 15)
    --json            JSON output
    -d                Skip validation, only git pull

EOF
}

invoke_lint() {
  local inner="$SCRIPT_DIR/linter-scripts/run.sh"
  if [ ! -f "$inner" ]; then
    echo "❌ Cannot find $inner" >&2
    exit 1
  fi
  exec "$inner" "$@"
}

has_command() {
  command -v "$1" >/dev/null 2>&1
}

open_url() {
  local url="$1"
  if   has_command xdg-open; then xdg-open "$url" >/dev/null 2>&1 &
  elif has_command open;     then open "$url" >/dev/null 2>&1 &
  elif has_command start;    then start "$url" >/dev/null 2>&1 &
  else
    echo "⚠️  no browser opener found (xdg-open/open/start). Visit $url manually."
  fi
}

invoke_slides() {
  echo ""
  echo "▸ slides — building offline deck and opening in browser"
  echo ""

  local slides_dir="$SCRIPT_DIR/slides-app"
  if [ ! -d "$slides_dir" ]; then
    echo "❌ slides-app/ not found at $slides_dir" >&2
    echo "   See spec-slides/00-overview.md for the slides spec." >&2
    exit 1
  fi

  echo "▸ git pull (best effort)..."
  git pull || echo "⚠️  git pull failed — continuing with local state"

  local runner=""
  if   has_command bun;  then runner="bun"
  elif has_command pnpm; then runner="pnpm"
  else
    echo "❌ Need 'bun' or 'pnpm' on PATH to build slides-app." >&2
    echo "   Install bun:  curl -fsSL https://bun.sh/install | bash" >&2
    exit 1
  fi
  echo "▸ using package runner: $runner"

  cd "$slides_dir"

  echo "▸ install dependencies..."
  "$runner" install

  echo "▸ build..."
  "$runner" run build

  echo "▸ start preview server (background)..."
  "$runner" run preview &
  local preview_pid=$!

  trap 'kill "$preview_pid" 2>/dev/null || true' EXIT INT TERM

  local url="http://localhost:4173/"
  local i=0
  while [ "$i" -lt 20 ]; do
    sleep 0.5
    if curl -fsSL --max-time 1 "$url" >/dev/null 2>&1; then
      break
    fi
    i=$((i + 1))
  done

  echo "▸ opening $url"
  open_url "$url"

  echo ""
  echo "▸ slides — preview running. Press Ctrl-C to stop."
  echo ""
  wait "$preview_pid"
}

# ── Dispatch ──────────────────────────────────────────────────────────
cmd="${1:-}"
case "$cmd" in
  "")            invoke_lint ;;
  lint)          shift; invoke_lint "$@" ;;
  slides)        shift; invoke_slides ;;
  help|-h|--help|-\?) show_help; exit 0 ;;
  -*)            invoke_lint "$@" ;;   # legacy flag form
  *)
    echo "❌ Unknown command: $cmd" >&2
    show_help
    exit 2
    ;;
esac
