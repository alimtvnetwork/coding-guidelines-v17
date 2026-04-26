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
set -euo pipefail

CACHE_FLAG="--cache-dir .cache/lint-placeholder"
DIFF_FLAG=""
LIST_ONLY=0
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
    -h|--help)
      sed -n '2,20p' "$0"; exit 0 ;;
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
idx=0
failed_label=""
failed_code=0

for entry in "${STEPS[@]}"; do
  idx=$((idx + 1))
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
  printf "\033[1;32m✅ lint-ci: all %d checks passed\033[0m\n" "$total"
  exit 0
else
  printf "\033[1;31m❌ lint-ci: failed at step %d/%d — %s (exit %d)\033[0m\n" \
    "$idx" "$total" "$failed_label" "$failed_code"
  echo "  Re-run only this step with the command shown above."
  exit "$failed_code"
fi
