#!/usr/bin/env bash
# ============================================================
# check-root-install-acceptance.sh
#
# Validates root install.sh / install.ps1 / linters-cicd/install.sh
# against spec/14-update/27-generic-installer-behavior.md:
#   §5.3 — --no-discovery / --no-main-fallback / --offline flags
#   §7   — startup banner with mode: / source: lines
#   §8   — exit-code header documents 0–5
# ============================================================

set -u
fail=0
pass=0

assert() {
    local label="$1" cond="$2"
    if eval "$cond"; then
        printf "  ✅ %s\n" "$label"
        pass=$((pass + 1))
    else
        printf "  ❌ %s\n" "$label"
        fail=$((fail + 1))
    fi
}

echo ""
echo "T8: root installer §27 conformance"

# ─── install.sh (Bash) ───────────────────────────────────────
F=install.sh
assert "[$F] §5.3 --no-discovery flag declared"     "grep -q -- '--no-discovery'        $F"
assert "[$F] §5.3 --no-main-fallback flag declared" "grep -q -- '--no-main-fallback'    $F"
assert "[$F] §5.3 --offline flag declared"          "grep -q -- '--offline'             $F"
assert "[$F] §5.3 --use-local-archive alias"        "grep -q -- '--use-local-archive'   $F"
assert "[$F] §7 banner has mode: line"              "grep -qE 'mode:[[:space:]]+\\\$INSTALL_MODE' $F"
assert "[$F] §7 banner has source: line"            "grep -qE 'source:[[:space:]]+\\\$SOURCE_KIND' $F"
assert "[$F] §8 EXIT CODES header"                  "grep -q 'EXIT CODES (spec §8)'     $F"
assert "[$F] §8 conforms-to header"                 "grep -q '27-generic-installer-behavior.md' $F"
assert "[$F] bash -n syntax clean"                  "bash -n $F 2>/dev/null"

# ─── install.ps1 (PowerShell) ────────────────────────────────
F=install.ps1
assert "[$F] §5.3 -NoDiscovery switch"              "grep -qE '\\[switch\\]\\\$NoDiscovery' $F"
assert "[$F] §5.3 -NoMainFallback switch"           "grep -qE '\\[switch\\]\\\$NoMainFallback' $F"
assert "[$F] §5.3 -Offline switch"                  "grep -qE '\\[switch\\]\\\$Offline'  $F"
assert "[$F] §5.3 -UseLocalArchive alias"           "grep -q  'UseLocalArchive'         $F"
assert "[$F] §7 banner has mode:"                   "grep -qE 'mode:[[:space:]]+\\\$installMode' $F"
assert "[$F] §7 banner has source:"                 "grep -qE 'source:[[:space:]]+\\\$sourceKind' $F"
assert "[$F] §8 EXIT CODES header"                  "grep -q 'EXIT CODES (spec §8)'     $F"
assert "[$F] §8 conforms-to header"                 "grep -q '27-generic-installer-behavior.md' $F"

# ─── linters-cicd/install.sh ─────────────────────────────────
F=linters-cicd/install.sh
assert "[$F] §7 banner has mode: line"              "grep -qE 'mode:[[:space:]]+\\\$INSTALL_MODE' $F"
assert "[$F] §7 banner has source: line"            "grep -qE 'source:[[:space:]]+\\\$SOURCE_KIND' $F"
assert "[$F] §8 EXIT CODES header"                  "grep -q 'EXIT CODES (spec §8)'     $F"
assert "[$F] §8 conforms-to header"                 "grep -q '27-generic-installer-behavior.md' $F"
assert "[$F] bash -n syntax clean"                  "bash -n $F 2>/dev/null"

echo ""
echo "  → $pass assertions passed, $fail failed"
exit $((fail > 0 ? 1 : 0))
