<#
.SYNOPSIS
    Pinned-version installer for GitHub Releases (PINNED MODE only).

.DESCRIPTION
    The release-page counterpart to install.ps1. ALWAYS runs in PINNED
    MODE per spec §3. Installs exactly the version it was built for
    (baked at release time) or the version explicitly passed via
    -Version. Per spec §4 it MUST NOT:
      • query /releases/latest
      • fall back to the main branch
      • cross repo boundaries (no V→V+N discovery)
      • pick a "compatible" or "nearest" version
      • silently downgrade to IMPLICIT MODE

    IMPLICIT MODE is unreachable here by design — use install.ps1 or one
    of the bundle installers if you want implicit-latest behavior.

    RESOLUTION ORDER (highest precedence first, spec §4.3):
      1. -Version <tag>          (CLI flag)
      2. $env:INSTALLER_VERSION  (env var, if set)
      3. v4.7.0 baked at release-asset build time
    If two sources disagree, a warning is emitted and the higher-
    precedence value wins.

    Spec: spec/14-update/25-release-pinned-installer.md
    Generic installer contract: spec/14-update/27-generic-installer-behavior.md

.PARAMETER Version
    [PINNED only — required if no baked tag] Install exactly this tag.
    Overrides the baked-in placeholder. Must match
    ^v?\\d+\\.\\d+\\.\\d+(-[A-Za-z0-9.]+)?$.

.PARAMETER NoUpdate
    No-op. Pinning is always on; switch accepted for ergonomics / parity
    with the bash variant.

.EXAMPLE
    irm https://github.com/<owner>/<repo>/releases/download/vX.Y.Z/release-install.ps1 | iex
    .\release-install.ps1 -Version v3.21.0

.NOTES
    Exit codes (per spec):
      0  success
      1  no version resolvable
      2  invalid version string
      3  pinned release / asset not found
      4  verification failed (raised by inner installer; spec §8)
      5  inner installer rejected pinning handshake
#>

param(
    [string]$Version = "",
    [switch]$NoUpdate,
    [Alias("?")]
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# ── Build-time substitution target ────────────────────────────────
# The release workflow replaces v4.7.0 with the concrete
# tag (e.g. v3.21.0) when uploading this file as a release asset.
$BakedVersion = "v4.7.0"

$Repo     = "alimtvnetwork/coding-guidelines-v15"
$SemverRe = '^v?\d+\.\d+\.\d+(-[A-Za-z0-9.]+)?$'

$script:Indent = "    "
function Write-Step { param([string]$Msg) Write-Host "$script:Indent▸ $Msg"  -ForegroundColor Cyan }
function Write-OK   { param([string]$Msg) Write-Host "$script:Indent✅ $Msg" -ForegroundColor Green }
function Write-Warn { param([string]$Msg) Write-Host "$script:Indent⚠️  $Msg" -ForegroundColor Yellow }
function Write-Err  { param([string]$Msg) Write-Host "$script:Indent❌ $Msg" -ForegroundColor Red }
function Write-Dim  { param([string]$Msg) Write-Host "$script:Indent$Msg"   -ForegroundColor DarkGray }

# ── -Help / -? short-circuit (spec §B.1.c.i) ──────────────────────
if ($Help) {
    Get-Help $PSCommandPath -Full
    exit 0
}

# ── Resolve pinned version (spec §Resolution Algorithm) ───────────
# Precedence (spec §B.2 + ratified env-var extension §B.2.b'):
#   1. -Version flag
#   2. $env:INSTALLER_VERSION
#   3. Baked v4.7.0
function Resolve-PinnedVersion {
    if ($Version) {
        if ($BakedVersion -ne "v4.7.0" -and $BakedVersion -ne $Version) {
            Write-Warn "Argument -Version ($Version) overrides baked-in ($BakedVersion)."
        }
        return $Version
    }
    if ($env:INSTALLER_VERSION) {
        if ($BakedVersion -ne "v4.7.0" -and $BakedVersion -ne $env:INSTALLER_VERSION) {
            Write-Warn "Env INSTALLER_VERSION ($($env:INSTALLER_VERSION)) overrides baked-in ($BakedVersion)."
        }
        return $env:INSTALLER_VERSION
    }
    if ($BakedVersion -ne "v4.7.0") {
        return $BakedVersion
    }
    return $null
}

$Resolved = Resolve-PinnedVersion
if (-not $Resolved) {
    Write-Err "release-install requires a pinned version."
    Write-Err "Pass -Version <tag> or run the baked copy from a Release page."
    exit 1
}

# ── Validate (spec §Validation) ───────────────────────────────────
if ($Resolved -notmatch $SemverRe) {
    Write-Err "Invalid version format: '$Resolved'"
    Write-Err "Expected semver, e.g. v3.21.0 or 3.21.0-beta.1"
    exit 2
}

Write-OK "Installing pinned version: $Resolved"

# ── Spec §7 banner ───────────────────────────────────────────────
Write-Host ""
Write-Host "  📦 release-install (pinned)" -ForegroundColor Cyan
Write-Host "     mode:    pinned"     -ForegroundColor Cyan
Write-Host "     repo:    $Repo"      -ForegroundColor Cyan
Write-Host "     version: $Resolved"  -ForegroundColor Cyan
Write-Host "     source:  release-asset" -ForegroundColor Cyan
Write-Host ""

# ── HEAD-check pinned asset (spec §4.1 dual endpoint) ────────────
# §4.1 REQUIRES: try /releases/download/<tag>/ first, then the tag
# tarball /archive/refs/tags/<tag>. Both URLs are bound to the SAME
# pinned tag — NOT a §4.2 main-branch / cross-repo fallback.
function Test-UrlExists {
    param([string]$Url)
    try {
        $req = [System.Net.HttpWebRequest]::Create($Url)
        $req.Method = "HEAD"
        $req.Timeout = 5000
        $req.AllowAutoRedirect = $true
        $resp = $req.GetResponse()
        $code = [int]$resp.StatusCode
        $resp.Close()
        return $code -eq 200
    } catch {
        return $false
    }
}

$PrimaryUrl  = "https://github.com/$Repo/releases/download/$Resolved/source-code.zip"
$TagZipUrl   = "https://codeload.github.com/$Repo/zip/refs/tags/$Resolved"

Write-Step "Probing primary release asset..."
$DownloadUrl = $null
if (Test-UrlExists -Url $PrimaryUrl) {
    $DownloadUrl = $PrimaryUrl
    Write-OK "Found release asset: $PrimaryUrl"
} else {
    Write-Warn "Primary asset unavailable — trying tag zip (still pinned to $Resolved)."
    if (Test-UrlExists -Url $TagZipUrl) {
        $DownloadUrl = $TagZipUrl
        Write-OK "Found tag zip: $TagZipUrl"
    } else {
        Write-Err "Release '$Resolved' not found at either location:"
        Write-Err "  primary:    $PrimaryUrl"
        Write-Err "  tag zip:    $TagZipUrl"
        Write-Err "Verify the tag exists at https://github.com/$Repo/releases"
        Write-Err "Per spec §4.2, this installer will NOT fall back to main or other tags."
        exit 3
    }
}

# ── Hand off to inner installer with pinning handshake ────────────
$InstallUrl = "https://raw.githubusercontent.com/$Repo/$Resolved/install.ps1"
Write-Step "Handing off to inner installer (pinned)..."
Write-Dim "  Source: $InstallUrl"
Write-Dim "  Pinned: $Resolved"

try {
    $script = Invoke-RestMethod -Uri $InstallUrl -UseBasicParsing
} catch {
    Write-Err "Could not download inner installer: $($_.Exception.Message)"
    exit 3
}

# Build a script block that invokes install.ps1 with pinning handshake.
$wrapper = @"
$script
# Hand-off override block injected by release-install.ps1
"@

try {
    $sb = [scriptblock]::Create($wrapper)
    & $sb -Version $Resolved -NoProbe -PinnedByReleaseInstall $Resolved
    $exit = $LASTEXITCODE
} catch {
    Write-Err "Inner installer error: $($_.Exception.Message)"
    exit 5
}

if ($exit -and $exit -ne 0) {
    Write-Err "Inner installer exited with code $exit"
    if ($exit -eq 2) {
        Write-Err "Pinning handshake may have been rejected (version skew?)"
        exit 5
    }
    exit $exit
}

Write-OK "Pinned install complete: $Resolved"
