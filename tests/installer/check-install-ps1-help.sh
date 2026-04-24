#!/usr/bin/env bash
# =====================================================================
# check-install-ps1-help.sh
#
# Verifies that `linters-cicd/install.ps1` honors `-Help`, `-h`, and
# `--help` by:
#   1. Exiting with code 0.
#   2. Printing usage text (contains "Usage:" and the script name).
#   3. Making ZERO network calls during help output.
#
# Network-call enforcement is implemented by overriding the cmdlets
# `Invoke-WebRequest` and `Invoke-RestMethod` in the PowerShell session
# BEFORE dot-sourcing the installer. Each override writes a marker file
# and throws — so any attempted probe both fails loudly AND leaves a
# file we can detect afterwards.
#
# Skips gracefully (exit 0) if PowerShell (`pwsh`) is not installed,
# matching the pattern used by other optional-toolchain checks in
# tests/installer/.
# =====================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
INSTALLER="$REPO_ROOT/linters-cicd/install.ps1"

if [ ! -f "$INSTALLER" ]; then
    echo "❌ installer not found: $INSTALLER" >&2
    exit 1
fi

# Locate pwsh, optionally falling back to nix.
PWSH=""
if command -v pwsh >/dev/null 2>&1; then
    PWSH="pwsh"
elif command -v nix >/dev/null 2>&1; then
    PWSH="nix run nixpkgs#powershell --"
else
    echo "⚠️  pwsh not installed; skipping install.ps1 help test (PASS by convention)"
    exit 0
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

NET_MARKER="$TMP_DIR/network-was-called"

# PowerShell wrapper script:
#   - Overrides Invoke-WebRequest / Invoke-RestMethod in this session so any
#     network probe writes a marker file AND throws. Function overrides take
#     precedence over cmdlets in the same session.
#   - Dot-sources / invokes the installer, propagating its exit code.
# The wrapper itself writes the installer's output to stdout (where we can
# capture it from bash) — we do not try to capture from inside PowerShell,
# because the script's `exit 0` terminates the host before we could inspect.
WRAPPER_FILE="$TMP_DIR/wrapper.ps1"
cat > "$WRAPPER_FILE" <<'PSEOF'
param([string]$Installer, [string]$Flag)

$ErrorActionPreference = 'Continue'

function Invoke-WebRequest {
    param([Parameter(ValueFromRemainingArguments=$true)]$AllArgs)
    Set-Content -Path $env:_NET_MARKER -Value "Invoke-WebRequest called: $AllArgs"
    throw "TEST: Invoke-WebRequest must not be called during --help"
}
function Invoke-RestMethod {
    param([Parameter(ValueFromRemainingArguments=$true)]$AllArgs)
    Set-Content -Path $env:_NET_MARKER -Value "Invoke-RestMethod called: $AllArgs"
    throw "TEST: Invoke-RestMethod must not be called during --help"
}

if ($Flag -eq '--help') {
    & $Installer --help
} elseif ($Flag -eq '-h') {
    & $Installer -h
} elseif ($Flag -eq '-Help') {
    & $Installer -Help
} else {
    Write-Error "unknown flag: $Flag"
    exit 2
}

exit $LASTEXITCODE
PSEOF

overall_rc=0
for flag in "-Help" "-h" "--help"; do
    rm -f "$NET_MARKER"
    echo ""
    echo "▸ Testing install.ps1 $flag"

    set +e
    # shellcheck disable=SC2086
    output=$(env _NET_MARKER="$NET_MARKER" $PWSH -NoProfile -File "$WRAPPER_FILE" \
        -Installer "$INSTALLER" \
        -Flag "$flag" 2>&1)
    flag_rc=$?
    set -e

    echo "----- captured output ($flag) -----"
    echo "$output"
    echo "----- exit=$flag_rc -----"

    if [ -f "$NET_MARKER" ]; then
        echo "❌ FAIL: $flag triggered a network call:"
        cat "$NET_MARKER"
        overall_rc=1
        continue
    fi

    if [ "$flag_rc" -ne 0 ]; then
        echo "❌ FAIL: $flag exited with $flag_rc (expected 0)"
        overall_rc=1
        continue
    fi

    # The PowerShell help output is aligned to bash `install.sh --help`
    # (same structure, same EXIT CODES section). Assert markers that exist
    # in BOTH installer flavors so this test stays in sync if we re-align
    # again.
    if ! echo "$output" | grep -q "============================================================"; then
        echo "❌ FAIL: $flag output missing banner rule (===…===) marker"
        overall_rc=1
        continue
    fi

    if ! echo "$output" | grep -q "^Flags:"; then
        echo "❌ FAIL: $flag output missing 'Flags:' section marker"
        overall_rc=1
        continue
    fi

    if ! echo "$output" | grep -q "EXIT CODES (spec §8):"; then
        echo "❌ FAIL: $flag output missing 'EXIT CODES (spec §8):' section marker"
        overall_rc=1
        continue
    fi

    echo "✅ PASS: $flag → exit 0, no network calls, usage printed"
done

if [ "$overall_rc" -eq 0 ]; then
    echo ""
    echo "✅ ALL: install.ps1 help variants exit 0 with zero network calls"
fi
exit "$overall_rc"