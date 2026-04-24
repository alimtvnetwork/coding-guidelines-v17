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

# PowerShell harness:
#   - Override IWR/IRM at the top of the session so any probe trips a marker + throws.
#   - Run the installer with the requested flag.
#   - Capture exit code; report PASS/FAIL based on (exit==0 && no marker && usage printed).
PS_HARNESS=$(cat <<'PSEOF'
param([string]$Installer, [string]$Flag, [string]$NetMarker)

$ErrorActionPreference = 'Continue'

# --- Network sentinels: fail loudly if the script tries to probe anything. ---
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
$env:_NET_MARKER = $NetMarker

# Run the installer with the requested help flag. Capture stdout for usage
# verification, let the script exit on its own.
try {
    if ($Flag -eq '--help') {
        # Bash long-form: pass via positional args so the script's UnboundArgs
        # / raw-line scanner picks it up.
        $output = & $Installer --help 2>&1
    } elseif ($Flag -eq '-h') {
        $output = & $Installer -h 2>&1
    } else {
        $output = & $Installer -Help 2>&1
    }
    $rc = $LASTEXITCODE
    if ($null -eq $rc) { $rc = 0 }
} catch {
    Write-Host "EXCEPTION: $_"
    $output = "$_"
    $rc = 99
}

$outText = ($output | Out-String)
Write-Host "----- captured output ($Flag) -----"
Write-Host $outText
Write-Host "----- exit=$rc -----"

if ($rc -ne 0) {
    Write-Host "FAIL: $Flag exited $rc (expected 0)"
    exit 1
}
if (-not ($outText -match 'Usage:')) {
    Write-Host "FAIL: $Flag output missing 'Usage:' marker"
    exit 1
}
if (-not ($outText -match 'install\.ps1')) {
    Write-Host "FAIL: $Flag output missing 'install.ps1' marker"
    exit 1
}

exit 0
PSEOF
)

HARNESS_FILE="$TMP_DIR/harness.ps1"
printf '%s\n' "$PS_HARNESS" > "$HARNESS_FILE"

overall_rc=0
for flag in "-Help" "-h" "--help"; do
    rm -f "$NET_MARKER"
    echo ""
    echo "▸ Testing install.ps1 $flag"

    # shellcheck disable=SC2086
    $PWSH -NoProfile -File "$HARNESS_FILE" \
        -Installer "$INSTALLER" \
        -Flag "$flag" \
        -NetMarker "$NET_MARKER"
    flag_rc=$?

    if [ -f "$NET_MARKER" ]; then
        echo "❌ FAIL: $flag triggered a network call:"
        cat "$NET_MARKER"
        overall_rc=1
        continue
    fi

    if [ "$flag_rc" -ne 0 ]; then
        echo "❌ FAIL: harness rc=$flag_rc for $flag"
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