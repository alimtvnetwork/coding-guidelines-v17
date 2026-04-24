<#
.SYNOPSIS
    linters-cicd installer (PowerShell, one-liner)

.DESCRIPTION
    Conforms to: spec/14-update/27-generic-installer-behavior.md

    Example one-liner:
      iwr -useb https://github.com/alimtvnetwork/coding-guidelines-v17/releases/latest/download/install.ps1 | iex

    Flags:
      -Dest <dir>         Install destination (default: ./linters-cicd)
      -Version <vX.Y.Z>   Install a specific version (PINNED MODE, §4) (default: latest)
      -NoVerify           Skip checksum verification (NOT recommended)
      -Help (-h, --help)  Show this help and exit (no network probe)

    EXIT CODES (spec §8):
      0  success
      1  generic failure (download / extract / checksum mismatch)
      2  unknown flag
      3  pinned release / asset not found (PINNED MODE only)
      4  verification failed (checksum)

.EXAMPLE
    .\install.ps1 -Help
    .\install.ps1 -Dest .\linters-cicd
    .\install.ps1 -Version v1.22.0
#>

param(
    [string]$Dest = "./linters-cicd",
    [string]$Version = "latest",
    [switch]$NoVerify,
    [Alias('h')]
    [switch]$Help
)

function Show-Usage {
    @"
linters-cicd installer (PowerShell)

Usage:
  install.ps1 [-Dest <dir>] [-Version <vX.Y.Z>] [-NoVerify] [-Help]

Flags:
  -Dest <dir>         Install destination (default: ./linters-cicd)
  -Version <vX.Y.Z>   Install a specific version (default: latest)
  -NoVerify           Skip checksum verification (NOT recommended)
  -Help, -h, --help   Show this help and exit

Examples:
  .\install.ps1 -Help
  .\install.ps1
  .\install.ps1 -Version v1.22.0
  .\install.ps1 -Dest .\linters-cicd -NoVerify
"@ | Write-Host
    exit 0
}

# Help is handled BEFORE any network probe / version lookup, so callers can
# safely run `install.ps1 --help` (or -h / -Help) with no internet access.
# This mirrors the bash installer behavior in `linters-cicd/install.sh`.
if ($Help) { Show-Usage }

# Bash-style long flag (`--help`) is not a valid PowerShell parameter name,
# so PowerShell may try to bind it as a positional value. Catch it by
# scanning the raw invocation line and the unbound-args list.
$rawLine = ''
if ($MyInvocation -and $MyInvocation.Line) { $rawLine = $MyInvocation.Line }
if ($rawLine -match '(^|\s)(--help|-\?|/\?)(\s|$)') { Show-Usage }
if ($Dest -in @('--help', '-?', '/?')) { Show-Usage }
if ($Version -in @('--help', '-?', '/?')) { Show-Usage }
if ($MyInvocation.UnboundArguments) {
    foreach ($a in $MyInvocation.UnboundArguments) {
        if ($a -in @('--help', '-?', '/?')) { Show-Usage }
    }
}

$ErrorActionPreference = 'Stop'

$Repo = "alimtvnetwork/coding-guidelines-v17"
$Verify = -not $NoVerify

# Banner (spec §7)
$installMode = "implicit"
$sourceKind  = "release-asset (latest)"
if ($Version -ne "latest") {
    $installMode = "pinned"
    $sourceKind  = "release-asset ($Version)"
}
Write-Host "    📦 coding-guidelines linters-cicd installer"
Write-Host "       mode:    $installMode"
Write-Host "       repo:    $Repo"
Write-Host "       version: $Version"
Write-Host "       source:  $sourceKind"
Write-Host "       dest:    $Dest"
Write-Host ""

if ($Version -eq "latest") {
    $urlBase = "https://github.com/$Repo/releases/latest/download"
} else {
    $urlBase = "https://github.com/$Repo/releases/download/$Version"
}

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("linters-cicd-" + [System.Guid]::NewGuid().ToString())
New-Item -ItemType Directory -Force -Path $tmp | Out-Null

try {
    Write-Host "    ▸ downloading zip..."
    $zipName = "coding-guidelines-linters.zip"
    $zipPath = Join-Path $tmp $zipName

    $downloadOk = $false
    if ($Version -eq "latest") {
        try {
            Invoke-WebRequest -UseBasicParsing -Uri "$urlBase/$zipName" -OutFile $zipPath
            $downloadOk = $true
        } catch { $downloadOk = $false }

        if (-not $downloadOk) {
            Write-Host "    ▸ resolving latest tag..."
            $rel = Invoke-RestMethod -UseBasicParsing -Uri "https://api.github.com/repos/$Repo/releases/latest"
            $tag = $rel.tag_name
            $zipName = "coding-guidelines-linters-$tag.zip"
            $urlBase = "https://github.com/$Repo/releases/download/$tag"
            $zipPath = Join-Path $tmp $zipName
            Invoke-WebRequest -UseBasicParsing -Uri "$urlBase/$zipName" -OutFile $zipPath
        }
    } else {
        $zipName = "coding-guidelines-linters-$Version.zip"
        $zipPath = Join-Path $tmp $zipName
        Invoke-WebRequest -UseBasicParsing -Uri "$urlBase/$zipName" -OutFile $zipPath
    }

    if ($Verify) {
        Write-Host "    ▸ verifying checksum..."
        $checksumPath = Join-Path $tmp "checksums.txt"
        try {
            Invoke-WebRequest -UseBasicParsing -Uri "$urlBase/checksums.txt" -OutFile $checksumPath
            $line = Select-String -Path $checksumPath -Pattern ([regex]::Escape($zipName)) | Select-Object -First 1
            if ($line) {
                $expected = ($line.Line -split '\s+')[0]
                $actual = (Get-FileHash -Algorithm SHA256 -Path $zipPath).Hash.ToLower()
                if ($expected -and ($expected.ToLower() -ne $actual)) {
                    Write-Error "    ❌ checksum mismatch! expected=$expected actual=$actual"
                    exit 4
                }
                Write-Host "    ✅ checksum OK"
            } else {
                Write-Host "    ⚠️  checksum line not found, skipping verification"
            }
        } catch {
            Write-Host "    ⚠️  checksums.txt not found, skipping verification"
        }
    }

    Write-Host "    ▸ extracting to $Dest..."
    if (-not (Test-Path $Dest)) { New-Item -ItemType Directory -Force -Path $Dest | Out-Null }
    Expand-Archive -Path $zipPath -DestinationPath $Dest -Force

    # Strip outer linters-cicd/ folder if present
    $nested = Join-Path $Dest "linters-cicd"
    if (Test-Path $nested) {
        Get-ChildItem -Path $nested -Force | ForEach-Object {
            Move-Item -Path $_.FullName -Destination $Dest -Force
        }
        Remove-Item -Recurse -Force $nested
    }

    Write-Host ""
    Write-Host "    ✅ installed → $Dest"
    Write-Host ""
    Write-Host "    Next steps:"
    Write-Host "       bash $Dest/run-all.sh --path . --format text"
    Write-Host ""
}
finally {
    Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
}