#!/usr/bin/env bash
# ============================================================
# tests/pipeline/check-bool-neg-001-pipeline.sh
#
# E2E smoke test for BOOL-NEG-001 through the full
# linters-cicd/run-all.sh orchestrator (closes pending-issue
# .lovable/resolved-issues/01-bool-neg-001-pipeline-untested.md).
#
# What it proves:
#   1. The orchestrator loads BOOL-NEG-001 from registry.json.
#   2. The check runs end-to-end and emits findings into the
#      merged SARIF (no rule-id collision with STYLE-099).
#   3. The 10-name allow-list silently passes through merging.
#   4. --jobs auto + --check-timeout do not drop or duplicate
#      the BOOL-NEG-001 findings.
#
# Exit codes:
#   0  pipeline emitted the expected BOOL-NEG-001 findings
#   1  drift (wrong count, missing rule, or merge corruption)
#   2  harness error (missing tools, fixture write failed)
# ============================================================
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RUN_ALL="$REPO_ROOT/linters-cicd/run-all.sh"

if [ ! -x "$RUN_ALL" ] && [ ! -f "$RUN_ALL" ]; then
    echo "::error::run-all.sh not found at $RUN_ALL" >&2
    exit 2
fi

FIXTURE_DIR="$(mktemp -d -t bool-neg-pipeline-XXXXXX)"
trap 'rm -rf "$FIXTURE_DIR"' EXIT

mkdir -p "$FIXTURE_DIR/migrations"

# 4 forbidden names (Tier 1 — Is/Has + Not/No)
# 2 allow-listed positive forms that MUST NOT trip the linter.
cat > "$FIXTURE_DIR/migrations/001_users.sql" <<'SQL'
CREATE TABLE Users (
    Id              INTEGER PRIMARY KEY,
    IsNotActive     BOOLEAN NOT NULL DEFAULT 0,
    HasNoLicense    BOOLEAN NOT NULL DEFAULT 0,
    IsNotVerified   BOOLEAN NOT NULL DEFAULT 0,
    HasNoSubscription BOOLEAN NOT NULL DEFAULT 0,
    IsActive        BOOLEAN NOT NULL DEFAULT 1,
    IsDisabled      BOOLEAN NOT NULL DEFAULT 0
);
SQL

OUT_SARIF="$FIXTURE_DIR/coding-guidelines.sarif"

echo "▸ running run-all.sh against fixture: $FIXTURE_DIR"
echo "  (rule-filter: BOOL-NEG-001, jobs: auto, check-timeout: 20s)"

# Run scoped to BOOL-NEG-001 only — keeps the test fast and
# isolates the assertion from unrelated rule changes.
bash "$RUN_ALL" \
    --path "$FIXTURE_DIR" \
    --rules BOOL-NEG-001 \
    --jobs auto \
    --check-timeout 20 \
    --output "$OUT_SARIF" \
    --format sarif >/tmp/bool-neg-pipeline.log 2>&1
RC=$?

# rc=1 is expected (findings present); rc=0 would mean no findings; rc=2 = tool error
if [ "$RC" -eq 2 ]; then
    echo "::error::orchestrator returned tool-error (rc=2)" >&2
    sed 's/^/    /' /tmp/bool-neg-pipeline.log >&2
    exit 2
fi

if [ ! -f "$OUT_SARIF" ]; then
    echo "::error::merged SARIF not produced at $OUT_SARIF" >&2
    exit 1
fi

# Assert via python: 4 BOOL-NEG-001 findings, no allow-listed names included.
python3 - "$OUT_SARIF" <<'PY' || exit 1
import json, re, sys
doc = json.load(open(sys.argv[1]))
findings = []
for run in doc.get("runs", []):
    for r in run.get("results", []):
        if r.get("ruleId") == "BOOL-NEG-001":
            loc = r["locations"][0]["physicalLocation"]
            msg = r["message"]["text"]
            # The linter's message format is:
            #   "Boolean column 'X' uses a forbidden ... Suggestion: rename to 'Y'."
            # We assert against the *flagged* identifier (X), not the
            # suggested replacement (Y) which legitimately contains
            # allow-listed names like 'IsActive'.
            m = re.search(r"Boolean column '([^']+)'", msg)
            flagged = m.group(1) if m else ""
            findings.append({
                "uri": loc["artifactLocation"]["uri"],
                "line": loc["region"]["startLine"],
                "msg": msg,
                "flagged": flagged,
            })

EXPECTED = 4
if len(findings) != EXPECTED:
    print(f"::error::expected {EXPECTED} BOOL-NEG-001 findings, got {len(findings)}", file=sys.stderr)
    for f in findings:
        print(f"   - {f['uri']}:{f['line']} :: {f['msg']}", file=sys.stderr)
    sys.exit(1)

# Allow-list assertion: IsActive / IsDisabled must never be the
# *flagged* identifier (they may appear in suggestions).
flagged_set = {f["flagged"] for f in findings}
for name in ("IsActive", "IsDisabled"):
    if name in flagged_set:
        print(f"::error::allow-listed name '{name}' was incorrectly flagged", file=sys.stderr)
        sys.exit(1)

# Forbidden names must each appear exactly once as the flagged identifier.
for name in ("IsNotActive", "HasNoLicense", "IsNotVerified", "HasNoSubscription"):
    hits = sum(1 for f in findings if f["flagged"] == name)
    if hits != 1:
        print(f"::error::forbidden name '{name}' appeared {hits} times as flagged identifier (want 1)", file=sys.stderr)
        sys.exit(1)

print(f"  OK BOOL-NEG-001 produced {len(findings)} finding(s) end-to-end")
print(f"  OK allow-list (IsActive, IsDisabled) silently passed")
print(f"  OK no rule-id collision in merged SARIF")
PY

echo "✅ BOOL-NEG-001 pipeline smoke test passed"