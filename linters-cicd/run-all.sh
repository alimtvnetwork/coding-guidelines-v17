#!/usr/bin/env bash
# ============================================================
# linters-cicd/run-all.sh
#
# Orchestrator — runs every check listed in checks/registry.json
# and merges results into a single SARIF 2.1.0 file. Supports
# inline suppressions, baseline diff, rule/language filters,
# parallel execution, and per-check timeouts.
#
# Usage:
#   ./run-all.sh [--path DIR] [--languages go,typescript]
#                [--rules CODE-RED-001,CODE-RED-004]
#                [--exclude-rules STYLE-002]
#                [--baseline .codeguidelines-baseline.sarif]
#                [--refresh-baseline .codeguidelines-baseline.sarif]
#                [--config .codeguidelines.toml]
#                [--jobs N|auto]            (default: 1, sequential)
#                [--check-timeout SECONDS]  (default: 20)
#                [--output coding-guidelines.sarif] [--format sarif|text]
#
# Exit codes:
#   0  no findings (or refresh-baseline mode)
#   1  one or more checks emitted findings
#   2  tool error (including check timeouts)
# ============================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PATH_ARG="."
LANGUAGES=""
RULES=""
EXCLUDE_RULES=""
EXCLUDE_PATHS=""
BASELINE=""
REFRESH_BASELINE=""
CONFIG_FILE=".codeguidelines.toml"
OUTPUT="coding-guidelines.sarif"
FORMAT="sarif"
JOBS="${LINTERS_JOBS:-1}"
CHECK_TIMEOUT="20"

while [ $# -gt 0 ]; do
    case "$1" in
        --path)              PATH_ARG="$2"; shift 2 ;;
        --languages)         LANGUAGES="$2"; shift 2 ;;
        --rules)             RULES="$2"; shift 2 ;;
        --exclude-rules)     EXCLUDE_RULES="$2"; shift 2 ;;
        --exclude-paths)     EXCLUDE_PATHS="$2"; shift 2 ;;
        --baseline)          BASELINE="$2"; shift 2 ;;
        --refresh-baseline)  REFRESH_BASELINE="$2"; shift 2 ;;
        --config)            CONFIG_FILE="$2"; shift 2 ;;
        --jobs)              JOBS="$2"; shift 2 ;;
        --check-timeout)     CHECK_TIMEOUT="$2"; shift 2 ;;
        --output)            OUTPUT="$2"; shift 2 ;;
        --format)            FORMAT="$2"; shift 2 ;;
        -h|--help)
            sed -n '2,26p' "$0"; exit 0 ;;
        *)
            echo "Unknown arg: $1" >&2; exit 2 ;;
    esac
done

if ! command -v python3 >/dev/null 2>&1; then
    echo "::error::python3 is required (>= 3.10)" >&2
    exit 2
fi

REGISTRY="$SCRIPT_DIR/checks/registry.json"
if [ ! -f "$REGISTRY" ]; then
    echo "::error::registry not found at $REGISTRY" >&2
    exit 2
fi

# ---- Resolve --jobs auto → max(1, nproc - 1) ----
if [ "$JOBS" = "auto" ]; then
    if command -v nproc >/dev/null 2>&1; then
        N=$(nproc)
        JOBS=$(( N > 1 ? N - 1 : 1 ))
    else
        JOBS=1
    fi
fi
case "$JOBS" in
    ''|*[!0-9]*) echo "::error::--jobs must be an integer or 'auto', got '$JOBS'" >&2; exit 2 ;;
esac
[ "$JOBS" -lt 1 ] && JOBS=1

# ---- Detect timeout binary (BSD/macOS may lack it) ----
TIMEOUT_BIN=""
if command -v timeout >/dev/null 2>&1; then
    TIMEOUT_BIN="timeout"
elif command -v gtimeout >/dev/null 2>&1; then
    TIMEOUT_BIN="gtimeout"
fi

# ---- Merge .codeguidelines.toml defaults with CLI flags ----
CONFIG_PATH="$PATH_ARG/$CONFIG_FILE"
CONFIG_OUT=$(python3 "$SCRIPT_DIR/scripts/load-config.py" \
    --config "$CONFIG_PATH" \
    --languages "$LANGUAGES" \
    --rules "$RULES" \
    --exclude-rules "$EXCLUDE_RULES" \
    --exclude-paths "$EXCLUDE_PATHS")
eval "$CONFIG_OUT"

TMP_DIR="$(mktemp -d)"
STATUS_DIR="$TMP_DIR/_status"
mkdir -p "$STATUS_DIR"
trap 'rm -rf "$TMP_DIR"' EXIT

EXIT=0
RAN=0

VERSION=$(cat "$SCRIPT_DIR/VERSION")
echo "    🔍 coding-guidelines linters-cicd v$VERSION"
echo "       path:           $PATH_ARG"
echo "       output:         $OUTPUT"
echo "       format:         $FORMAT"
echo "       languages:      ${LANGUAGES:-auto}"
echo "       rules:          ${RULES:-all}"
echo "       exclude-rules:  ${EXCLUDE_RULES:-none}"
echo "       exclude-paths:  ${EXCLUDE_PATHS:-none}"
echo "       jobs:           $JOBS"
echo "       check-timeout:  ${CHECK_TIMEOUT}s"
[ -n "$BASELINE" ]         && echo "       baseline:       $BASELINE"
[ -n "$REFRESH_BASELINE" ] && echo "       refresh:        $REFRESH_BASELINE"
[ -z "$TIMEOUT_BIN" ]      && echo "       ⚠️  no 'timeout' binary — running without per-check timeout"
echo ""

# Iterate registry via python (no jq dependency)
SCRIPTS=$(python3 - "$REGISTRY" "$LANGUAGES" "$RULES" <<'PY'
import json, sys
registry_path, langs_csv, rules_csv = sys.argv[1], sys.argv[2], sys.argv[3]
wanted_langs = {l.strip() for l in langs_csv.split(",") if l.strip()}
wanted_rules = {r.strip() for r in rules_csv.split(",") if r.strip()}
with open(registry_path) as f:
    reg = json.load(f)
for rule_id, meta in reg.items():
    if wanted_rules and rule_id not in wanted_rules:
        continue
    for lang, script in meta["languages"].items():
        if wanted_langs and lang != "universal" and lang not in wanted_langs:
            continue
        print(f"{rule_id}|{lang}|{script}")
PY
)

# ---- Single check runner: writes SARIF to OUT, status code to STATUS_DIR ----
run_check() {
    local rule_id="$1" lang="$2" script_path="$3" out_path="$4" status_path="$5"
    local rc
    if [ -n "$TIMEOUT_BIN" ]; then
        "$TIMEOUT_BIN" -k 2 "$CHECK_TIMEOUT" \
            python3 "$script_path" --path "$PATH_ARG" --format sarif --output "$out_path" --exclude-paths "$EXCLUDE_PATHS"
        rc=$?
    else
        python3 "$script_path" --path "$PATH_ARG" --format sarif --output "$out_path" --exclude-paths "$EXCLUDE_PATHS"
        rc=$?
    fi
    # 124 = GNU timeout overrun, 137 = SIGKILL grace, 143 = SIGTERM grace
    if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ] || [ "$rc" -eq 143 ]; then
        python3 "$SCRIPT_DIR/scripts/emit-timeout.py" \
            "$rule_id" "$lang" "$CHECK_TIMEOUT" "$out_path" "$VERSION"
        rc=124
    fi
    echo "$rc" > "$status_path"
}
export -f run_check
export PATH_ARG SCRIPT_DIR CHECK_TIMEOUT TIMEOUT_BIN VERSION EXCLUDE_PATHS

# ---- Build the work list ----
WORK_LIST="$TMP_DIR/_worklist.txt"
> "$WORK_LIST"
while IFS='|' read -r RULE_ID LANG SCRIPT; do
    [ -z "$RULE_ID" ] && continue
    SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT"
    if [ ! -f "$SCRIPT_PATH" ]; then
        echo "    ⚠️  skipped $RULE_ID/$LANG — script missing"
        continue
    fi
    echo "$RULE_ID|$LANG|$SCRIPT_PATH" >> "$WORK_LIST"
done <<< "$SCRIPTS"

TOTAL=$(wc -l < "$WORK_LIST" | tr -d ' ')

# ---- Sequential vs parallel dispatch ----
if [ "$JOBS" -eq 1 ]; then
    while IFS='|' read -r RULE_ID LANG SCRIPT_PATH; do
        [ -z "$RULE_ID" ] && continue
        OUT="$TMP_DIR/$RULE_ID-$LANG.sarif"
        STATUS="$STATUS_DIR/$RULE_ID-$LANG.rc"
        RAN=$((RAN + 1))
        printf "    ▸ %-30s %-12s ... " "$RULE_ID" "$LANG"
        run_check "$RULE_ID" "$LANG" "$SCRIPT_PATH" "$OUT" "$STATUS" >/dev/null 2>&1
        rc=$(cat "$STATUS")
        case "$rc" in
            0)   echo "✅ clean" ;;
            1)   COUNT=$(python3 -c "import json; print(len(json.load(open('$OUT'))['runs'][0]['results']))")
                 echo "❌ $COUNT raw finding(s)" ;;
            124) echo "⏱  timeout (>${CHECK_TIMEOUT}s)"; EXIT=2 ;;
            *)   echo "‼️  tool error (rc=$rc)"; EXIT=2 ;;
        esac
    done < "$WORK_LIST"
else
    echo "    ▸ dispatching $TOTAL check(s) across $JOBS worker(s)..."
    # xargs -P for parallel dispatch; each line is one job
    # -P parallel workers, one bash invocation per line, line passed as $0
    xargs -P "$JOBS" -I {} bash -c '
            line="$1"
            rule_id=$(echo "$line" | cut -d"|" -f1)
            lang=$(echo "$line" | cut -d"|" -f2)
            script_path=$(echo "$line" | cut -d"|" -f3)
            out="'"$TMP_DIR"'/${rule_id}-${lang}.sarif"
            status="'"$STATUS_DIR"'/${rule_id}-${lang}.rc"
            run_check "$rule_id" "$lang" "$script_path" "$out" "$status" >/dev/null 2>&1
        ' _ {} < "$WORK_LIST"
    # Render results in registry order for stable logs
    while IFS='|' read -r RULE_ID LANG SCRIPT_PATH; do
        [ -z "$RULE_ID" ] && continue
        OUT="$TMP_DIR/$RULE_ID-$LANG.sarif"
        STATUS="$STATUS_DIR/$RULE_ID-$LANG.rc"
        RAN=$((RAN + 1))
        printf "    ▸ %-30s %-12s ... " "$RULE_ID" "$LANG"
        rc=$(cat "$STATUS" 2>/dev/null || echo "?")
        case "$rc" in
            0)   echo "✅ clean" ;;
            1)   COUNT=$(python3 -c "import json; print(len(json.load(open('$OUT'))['runs'][0]['results']))" 2>/dev/null || echo "?")
                 echo "❌ $COUNT raw finding(s)" ;;
            124) echo "⏱  timeout (>${CHECK_TIMEOUT}s)"; EXIT=2 ;;
            *)   echo "‼️  tool error (rc=$rc)"; EXIT=2 ;;
        esac
    done < "$WORK_LIST"
fi

echo ""
echo "    ────────────────────────────────────────────────"

# Merge all per-tool SARIF files into one (always SARIF here so
# post-processing can run; format conversion happens after)
python3 "$SCRIPT_DIR/scripts/merge-sarif.py" "$TMP_DIR" "$OUTPUT" "sarif"

# Apply suppressions, exclude-rules, baseline
POST_ARGS=(--sarif "$OUTPUT" --path "$PATH_ARG" --exclude-rules "$EXCLUDE_RULES")
[ -n "$BASELINE" ]         && POST_ARGS+=(--baseline "$BASELINE")
[ -n "$REFRESH_BASELINE" ] && POST_ARGS+=(--refresh-baseline "$REFRESH_BASELINE")

if python3 "$SCRIPT_DIR/scripts/post-process.py" "${POST_ARGS[@]}"; then
    POST_RC=0
else
    POST_RC=$?
fi

# If user requested text output, re-render from the post-processed SARIF
if [ "$FORMAT" = "text" ] && [ -z "$REFRESH_BASELINE" ]; then
    python3 - "$OUTPUT" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1]))
total = 0
out_lines = []
for run in doc.get("runs", []):
    tool = run["tool"]["driver"]["name"]
    results = run.get("results", [])
    total += len(results)
    if not results:
        out_lines.append(f"✅ {tool}: clean")
        continue
    out_lines.append(f"❌ {tool}: {len(results)} finding(s)")
    for r in results:
        loc = r["locations"][0]["physicalLocation"]
        uri = loc["artifactLocation"]["uri"]
        line = loc["region"]["startLine"]
        out_lines.append(f"   [{r['level']}] {uri}:{line}  {r['ruleId']}  {r['message']['text']}")
out_lines.append("")
out_lines.append(f"Total: {total} finding(s)")
open(sys.argv[1], "w").write("\n".join(out_lines))
PY
fi

if [ -n "$REFRESH_BASELINE" ]; then
    echo "    📌 baseline refreshed → $REFRESH_BASELINE"
    echo "    🏁 ran $RAN check(s) — exit 0"
    exit 0
fi

if [ "$EXIT" -ne 2 ] && [ "$POST_RC" -eq 1 ]; then
    EXIT=1
fi

echo "    📄 merged → $OUTPUT"
echo "    🏁 ran $RAN check(s) — exit $EXIT"
exit "$EXIT"
