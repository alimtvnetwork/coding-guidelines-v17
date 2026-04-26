#!/usr/bin/env bash
# scripts/lint-ci.sh
#
# Run every linter-scripts/* check in the same order as the `lint` job in
# .github/workflows/ci.yml, plus the cross-link checker from the
# `cross-links` job. Halts on the first failure (matches CI semantics).
#
# Wired into package.json as `npm run lint:ci`. Keep this script in
# lockstep with ci.yml — a drift check in CI itself is left as a
# follow-up, but for now any new step added to ci.yml MUST be appended
# here in the same position so local runs catch the same regressions.
#
# Exit codes:
#   0  all checks passed
#   N  the Nth check failed (script exits with that check's exit code)
#
# Usage:
#   bash scripts/lint-ci.sh           # run everything
#   bash scripts/lint-ci.sh --list    # print the ordered step list and exit
#   bash scripts/lint-ci.sh --no-cache  # disable placeholder-linter cache
#   bash scripts/lint-ci.sh --diff-base <ref>
#                                     # diff-mode placeholder lint vs. <ref>
#                                     # (e.g. origin/main, HEAD~1) — only
#                                     # changed `.md` files emit per-file
#                                     # violations; cross-file P-007 still
#                                     # walks the full tree.
#   bash scripts/lint-ci.sh --step N        # run ONLY the Nth step
#   bash scripts/lint-ci.sh --step N-M      # run ONLY steps N through M
#   bash scripts/lint-ci.sh --from N        # run from step N to the end
#   bash scripts/lint-ci.sh --to M          # run from step 1 to step M
#   bash scripts/lint-ci.sh --from N --to M # run steps N through M
#                                     # Step numbers come from `--list`
#                                     # (1-indexed, inclusive on both ends).
#                                     # `--step` is mutually exclusive with
#                                     # `--from`/`--to`. Use to re-run only
#                                     # the failing step range without
#                                     # editing this script.
set -euo pipefail

CACHE_FLAG="--cache-dir .cache/lint-placeholder"
DIFF_FLAG=""
LIST_ONLY=0
# Range bounds are populated from --step / --from / --to. Empty = unbounded
# on that end (so the default RUN_FROM=1 / RUN_TO=<total> covers the
# pre-existing "run everything" behaviour).
RUN_FROM=""
RUN_TO=""
RANGE_SOURCE=""  # "step" or "from-to"; tracked for the mutual-exclusion check.

# Parse a step token: either "N" or "N-M". Echoes "<from> <to>" on
# success, exits 2 on malformed input. Bounds are validated against
# the step total in a second pass once STEPS is known.
_parse_step_range() {
  local token="$1" flag="$2"
  if [[ "$token" =~ ^([0-9]+)$ ]]; then
    echo "${BASH_REMATCH[1]} ${BASH_REMATCH[1]}"
  elif [[ "$token" =~ ^([0-9]+)-([0-9]+)$ ]]; then
    echo "${BASH_REMATCH[1]} ${BASH_REMATCH[2]}"
  else
    echo "::error::$flag expects N or N-M (got '$token')" >&2
    exit 2
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --list)     LIST_ONLY=1 ;;
    --no-cache) CACHE_FLAG="" ;;
    --diff-base)
      shift
      [[ $# -gt 0 ]] || { echo "::error::--diff-base needs a ref" >&2; exit 2; }
      DIFF_FLAG="--diff-base $1"
      ;;
    --diff-base=*)
      DIFF_FLAG="--diff-base ${1#--diff-base=}"
      ;;
    --step)
      shift
      [[ $# -gt 0 ]] || { echo "::error::--step needs N or N-M" >&2; exit 2; }
      read -r RUN_FROM RUN_TO < <(_parse_step_range "$1" --step)
      RANGE_SOURCE="step"
      ;;
    --step=*)
      read -r RUN_FROM RUN_TO < <(_parse_step_range "${1#--step=}" --step)
      RANGE_SOURCE="step"
      ;;
    --from)
      shift
      [[ $# -gt 0 ]] || { echo "::error::--from needs N" >&2; exit 2; }
      [[ "$1" =~ ^[0-9]+$ ]] || { echo "::error::--from expects N (got '$1')" >&2; exit 2; }
      [[ "$RANGE_SOURCE" == "step" ]] && { echo "::error::--from cannot be combined with --step" >&2; exit 2; }
      RUN_FROM="$1"
      RANGE_SOURCE="from-to"
      ;;
    --from=*)
      v="${1#--from=}"
      [[ "$v" =~ ^[0-9]+$ ]] || { echo "::error::--from expects N (got '$v')" >&2; exit 2; }
      [[ "$RANGE_SOURCE" == "step" ]] && { echo "::error::--from cannot be combined with --step" >&2; exit 2; }
      RUN_FROM="$v"
      RANGE_SOURCE="from-to"
      ;;
    --to)
      shift
      [[ $# -gt 0 ]] || { echo "::error::--to needs M" >&2; exit 2; }
      [[ "$1" =~ ^[0-9]+$ ]] || { echo "::error::--to expects M (got '$1')" >&2; exit 2; }
      [[ "$RANGE_SOURCE" == "step" ]] && { echo "::error::--to cannot be combined with --step" >&2; exit 2; }
      RUN_TO="$1"
      RANGE_SOURCE="from-to"
      ;;
    --to=*)
      v="${1#--to=}"
      [[ "$v" =~ ^[0-9]+$ ]] || { echo "::error::--to expects M (got '$v')" >&2; exit 2; }
      [[ "$RANGE_SOURCE" == "step" ]] && { echo "::error::--to cannot be combined with --step" >&2; exit 2; }
      RUN_TO="$v"
      RANGE_SOURCE="from-to"
      ;;
    -h|--help)
      sed -n '2,32p' "$0"; exit 0 ;;
    *)
      echo "::error::unknown flag: $1" >&2; exit 2 ;;
  esac
  shift
done

# Step registry: each entry is "label|command". Order MUST match
# .github/workflows/ci.yml. Steps that intentionally don't fail CI
# (e.g. the advisory Python validator) carry `|| true` inline.
STEPS=(
  "Verify linter scripts present|bash scripts/lint-ci-verify-present.sh"
  "Run Go validator (spec)|go run linter-scripts/validate-guidelines.go --path spec --max-lines 15"
  "Run Python validator (spec, advisory)|python3 linter-scripts/validate-guidelines.py spec || true"
  "Run Axios version check|bash linter-scripts/check-axios-version.sh"
  "Check spec folder references (stale-link guard)|python3 linter-scripts/check-spec-folder-refs.py"
  "Check forbidden spec paths (re-split + merge-proposal guard)|bash linter-scripts/check-forbidden-spec-paths.sh"
  "Check forbidden strings (TOML-driven rename guards)|python3 linter-scripts/check-forbidden-strings.py"
  "Check README install section (position + one-line fences)|python3 linter-scripts/check-readme-install-section.py"
  "Check spec placeholder comments (P-001 … P-008)|python3 linter-scripts/check-placeholder-comments.py ${DIFF_FLAG} ${CACHE_FLAG}"
  "Validate spec internal cross-references|python3 linter-scripts/check-spec-cross-links.py --root spec --repo-root ."
)

if [[ "$LIST_ONLY" == "1" ]]; then
  printf '%s\n' "${STEPS[@]}" | nl -ba -s'. ' | sed 's/|.*//'
  exit 0
fi

total=${#STEPS[@]}

# ---- Resolve and validate the requested range against the registry ----
# Defaults: empty bounds = unbounded → cover the full registry, which
# preserves the pre-flag behaviour of "run everything".
[[ -z "$RUN_FROM" ]] && RUN_FROM=1
[[ -z "$RUN_TO"   ]] && RUN_TO="$total"
if (( RUN_FROM < 1 || RUN_FROM > total )); then
  echo "::error::step $RUN_FROM out of range (registry has $total step(s); see --list)" >&2
  exit 2
fi
if (( RUN_TO < 1 || RUN_TO > total )); then
  echo "::error::step $RUN_TO out of range (registry has $total step(s); see --list)" >&2
  exit 2
fi
if (( RUN_FROM > RUN_TO )); then
  echo "::error::range start ($RUN_FROM) is after range end ($RUN_TO)" >&2
  exit 2
fi
if (( RUN_FROM != 1 || RUN_TO != total )); then
  printf "\033[1;33mℹ️  lint-ci: running steps %d–%d of %d (subset mode)\033[0m\n" \
    "$RUN_FROM" "$RUN_TO" "$total"
fi

idx=0
failed_label=""
failed_code=0

for entry in "${STEPS[@]}"; do
  idx=$((idx + 1))
  # Honour the requested range. We still increment `idx` for skipped
  # steps so the displayed numbering matches `--list`, which is what
  # the user typed on the CLI.
  if (( idx < RUN_FROM || idx > RUN_TO )); then
    continue
  fi
  label="${entry%%|*}"
  cmd="${entry#*|}"
  printf "\n\033[1;36m[lint-ci %d/%d]\033[0m %s\n" "$idx" "$total" "$label"
  printf "  $ %s\n" "$cmd"
  # `set +e` so we can capture the exit code, run the forbidden-strings
  # summary on failure, and report a clean error message.
  set +e
  bash -c "$cmd"
  rc=$?
  set -e
  if [[ $rc -ne 0 ]]; then
    failed_label="$label"
    failed_code=$rc
    # Mirror the CI step "Forbidden-strings summary report (on failure)".
    if [[ "$label" == "Check forbidden strings"* ]]; then
      echo ""
      echo "--- Forbidden-strings summary (CI-equivalent on-failure step) ---"
      python3 linter-scripts/forbidden-strings-summary.py --markdown || true
    fi
    break
  fi
done

echo ""
if [[ -z "$failed_label" ]]; then
  if (( RUN_FROM == 1 && RUN_TO == total )); then
    printf "\033[1;32m✅ lint-ci: all %d checks passed\033[0m\n" "$total"
  else
    printf "\033[1;32m✅ lint-ci: subset steps %d–%d passed (%d of %d total)\033[0m\n" \
      "$RUN_FROM" "$RUN_TO" "$((RUN_TO - RUN_FROM + 1))" "$total"
    echo "  Run without --step/--from/--to to verify the full pipeline before pushing."
  fi
  exit 0
else
  printf "\033[1;31m❌ lint-ci: failed at step %d/%d — %s (exit %d)\033[0m\n" \
    "$idx" "$total" "$failed_label" "$failed_code"
  echo "  Re-run only this step with: bash scripts/lint-ci.sh --step $idx"
  if (( idx < total )); then
    echo "  Or resume from here with:    bash scripts/lint-ci.sh --from $idx"
  fi
  exit "$failed_code"
fi
