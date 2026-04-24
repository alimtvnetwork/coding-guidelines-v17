#!/usr/bin/env bash
# =====================================================================
# check-install-ps1-noverify-help.sh
#
# Verifies that `linters-cicd/install.ps1`, when invoked with -NoVerify
# combined with any help flag (-Help, -h, --help), still:
#
#   1. Exits with code 0.
#   2. Prints usage text (banner rule, "Flags:", "EXIT CODES (spec §8):").
#   3. Makes ZERO network calls.
#   4. NEVER prints the prominent -NoVerify warning banner — help output
#      must not be polluted by runtime warnings, because help can be
#      invoked offline / in CI introspection / from documentation tools.
#
# The banner sentinel asserted here ("WARNING: -NoVerify") is a stable
# substring of the warning block in install.ps1; if that copy changes,
# update both the installer and this sentinel together.
#
# Network-call enforcement uses the same Invoke-WebRequest /
# Invoke-RestMethod override pattern as check-install-ps1-help.sh.
#
# Skips gracefully (exit 0) when PowerShell (`pwsh`) is not installed,
# matching the convention used by other optional-toolchain checks in
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
    echo "⚠️  pwsh not installed; skipping install.ps1 -NoVerify+help test (PASS by convention)"
    exit 0
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

NET_MARKER="$TMP_DIR/network-was-called"

# PowerShell wrapper:
#   - Overrides Invoke-WebRequest / Invoke-RestMethod so any network probe
#     writes a marker file AND throws.
#   - Dispatches the installer with -NoVerify plus the requested help flag.
#     Each help-flag form is invoked verbatim so PowerShell parameter
#     binding mirrors a real operator invocation (-Help via parameter,
#     -h via [Alias], --help via the unbound-args sniffer in install.ps1).
WRAPPER_FILE="$TMP_DIR/wrapper.ps1"
cat > "$WRAPPER_FILE" <<'PSEOF'
param([string]$Installer, [string]$Flag)

$ErrorActionPreference = 'Continue'

function Invoke-WebRequest {
    param([Parameter(ValueFromRemainingArguments=$true)]$AllArgs)
    Set-Content -Path $env:_NET_MARKER -Value "Invoke-WebRequest called: $AllArgs"
    throw "TEST: Invoke-WebRequest must not be called during help"
}
function Invoke-RestMethod {
    param([Parameter(ValueFromRemainingArguments=$true)]$AllArgs)
    Set-Content -Path $env:_NET_MARKER -Value "Invoke-RestMethod called: $AllArgs"
    throw "TEST: Invoke-RestMethod must not be called during help"
}

# Order matters: -NoVerify is a switch and must be listed alongside the
# help flag. The installer is expected to short-circuit to Show-Usage
# BEFORE consulting the $NoVerify switch, regardless of arg order.
if ($Flag -eq '--help') {
    & $Installer -NoVerify --help
} elseif ($Flag -eq '-h') {
    & $Installer -NoVerify -h
} elseif ($Flag -eq '-Help') {
    & $Installer -NoVerify -Help
} elseif ($Flag -eq '--help-first') {
    # Reverse order: help flag BEFORE -NoVerify, to confirm position
    # independence.
    & $Installer --help -NoVerify
} elseif ($Flag -eq '-h-first') {
    & $Installer -h -NoVerify
} elseif ($Flag -eq '-Help-first') {
    & $Installer -Help -NoVerify
} else {
    Write-Error "unknown flag: $Flag"
    exit 2
}

exit $LASTEXITCODE
PSEOF

overall_rc=0
# Test every help-flag form, in BOTH orderings relative to -NoVerify.
for flag in "-Help" "-h" "--help" "-Help-first" "-h-first" "--help-first"; do
    rm -f "$NET_MARKER"
    echo ""
    echo "▸ Testing install.ps1 with -NoVerify + $flag"

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

    # Help body must be present.
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

    # CRITICAL: the -NoVerify warning banner must NOT appear in help output.
    # Sentinel substring is the unique warning headline from install.ps1.
    if echo "$output" | grep -q "WARNING: -NoVerify"; then
        echo "❌ FAIL: $flag printed the -NoVerify warning banner during help"
        echo "        (banner must only fire on a real install run)"
        overall_rc=1
        continue
    fi

    # Defense in depth: also assert the install banner ("📦 coding-guidelines
    # linters-cicd installer") never prints during help — same reasoning.
    if echo "$output" | grep -q "coding-guidelines linters-cicd installer"; then
        echo "❌ FAIL: $flag printed the install banner during help"
        overall_rc=1
        continue
    fi

    echo "✅ PASS: $flag → exit 0, no network, usage shown, no NoVerify banner"
done

if [ "$overall_rc" -eq 0 ]; then
    echo ""
    echo "✅ ALL: install.ps1 -NoVerify + help variants exit 0 with"
    echo "        no network calls and no -NoVerify warning banner"
fi
exit "$overall_rc"