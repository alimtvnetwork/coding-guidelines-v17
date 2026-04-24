<#
.SYNOPSIS
    Download specific folders from a GitHub repo and merge into local directory.

.DESCRIPTION
    Reads install-config.json for source repo, branch, and folder list.
    Downloads the repo archive, extracts configured folders, and merges
    them into the current working directory. Existing files are overwritten;
    existing folders are preserved and merged.

.EXAMPLE
    .\install.ps1
    .\install.ps1 -Repo "alimtvnetwork/coding-guidelines-v17" -Branch "dev"
    .\install.ps1 -ConfigFile "my-config.json"
    irm https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v17/main/install.ps1 | iex
#>

param(
    [string]$Repo = "",
    [string]$Branch = "",
    [string]$ConfigFile = "install-config.json",
    [string[]]$Folders = @()
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# ── Helper functions ──────────────────────────────────────────────

function Write-Step  { param([string]$Msg) Write-Host "▸ $Msg" -ForegroundColor Cyan }
function Write-OK    { param([string]$Msg) Write-Host "✅ $Msg" -ForegroundColor Green }
function Write-Warn  { param([string]$Msg) Write-Host "⚠️  $Msg" -ForegroundColor Yellow }
function Write-Err   { param([string]$Msg) Write-Host "❌ $Msg" -ForegroundColor Red }

# ── Read config ───────────────────────────────────────────────────

function Read-InstallConfig {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return $null
    }

    $raw = Get-Content -Path $Path -Raw
    $cfg = $raw | ConvertFrom-Json
    return $cfg
}

# ── Load config ───────────────────────────────────────────────────

$config = $null
if (Test-Path $ConfigFile) {
    Write-Step "Reading config from $ConfigFile"
    $config = Read-InstallConfig -Path $ConfigFile
}
else {
    Write-Warn "No config file found at $ConfigFile — using defaults"
}

# Apply config values (CLI params take priority)
if ([string]::IsNullOrEmpty($Repo)) {
    $Repo = if ($config -and $config.repo) { $config.repo } else { "alimtvnetwork/coding-guidelines-v17" }
}

if ([string]::IsNullOrEmpty($Branch)) {
    $Branch = if ($config -and $config.branch) { $config.branch } else { "main" }
}

if ($Folders.Count -eq 0) {
    if ($config -and $config.folders) {
        $Folders = @($config.folders)
    }
    else {
        $Folders = @("spec", "linters", "linter-scripts")
    }
}

# ── Banner ────────────────────────────────────────────────────────

Write-Host ""
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor White
Write-Host "  Spec & Scripts Installer" -ForegroundColor White
Write-Host "  Source:  $Repo (branch: $Branch)" -ForegroundColor White
Write-Host "  Folders: $($Folders -join ', ')" -ForegroundColor White
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor White
Write-Host ""

# ── Step 1: Check for GitHub release ──────────────────────────────

Write-Step "Checking for GitHub releases..."

$releaseArchiveUrl = ""
$releaseApiUrl = "https://api.github.com/repos/$Repo/releases/latest"

try {
    $releaseResponse = Invoke-RestMethod -Uri $releaseApiUrl -Method Get -ErrorAction Stop
    if ($releaseResponse.zipball_url) {
        Write-OK "Release found — downloading release archive"
        $releaseArchiveUrl = $releaseResponse.zipball_url
    }
}
catch {
    # No release found — continue with branch archive
}

# ── Step 2: Download archive ──────────────────────────────────────

$tmpDir = Join-Path ([System.IO.Path]::GetTempPath()) ("install-" + [guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
$archivePath = Join-Path $tmpDir "repo.zip"

try {
    if ($releaseArchiveUrl -ne "") {
        Write-Step "Downloading release archive..."
        Invoke-WebRequest -Uri $releaseArchiveUrl -OutFile $archivePath -UseBasicParsing
    }
    else {
        Write-Step "No release found — downloading branch archive..."
        $archiveUrl = "https://github.com/$Repo/archive/refs/heads/$Branch.zip"
        Invoke-WebRequest -Uri $archiveUrl -OutFile $archivePath -UseBasicParsing
    }

    # ── Step 3: Extract archive ───────────────────────────────────

    Write-Step "Extracting archive..."
    $extractDir = Join-Path $tmpDir "extracted"
    Expand-Archive -Path $archivePath -DestinationPath $extractDir -Force

    # Find the root directory inside the archive
    $archiveRoot = Get-ChildItem -Path $extractDir -Directory | Select-Object -First 1

    if (-not $archiveRoot) {
        Write-Err "Failed to find extracted archive root"
        exit 1
    }

    # ── Step 4: Copy folders ──────────────────────────────────────

    $destDir = Get-Location
    $copied = 0
    $skipped = 0

    foreach ($folder in $Folders) {
        $srcPath = Join-Path $archiveRoot.FullName $folder

        if (-not (Test-Path $srcPath)) {
            Write-Warn "Folder '$folder' not found in source repo — skipping"
            $skipped++
            continue
        }

        Write-Step "Merging folder: $folder"
        $destPath = Join-Path $destDir $folder

        # Ensure destination exists
        if (-not (Test-Path $destPath)) {
            New-Item -ItemType Directory -Path $destPath -Force | Out-Null
        }

        # Recursively copy/merge files
        Get-ChildItem -Path $srcPath -Recurse -File | ForEach-Object {
            $relativePath = $_.FullName.Substring($srcPath.Length)
            $targetFile = Join-Path $destPath $relativePath
            $targetDir = Split-Path $targetFile -Parent

            if (-not (Test-Path $targetDir)) {
                New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
            }

            Copy-Item -Path $_.FullName -Destination $targetFile -Force
        }

        Write-OK "Merged $folder"
        $copied++
    }

    # ── Summary ───────────────────────────────────────────────────

    Write-Host ""
    Write-Host "════════════════════════════════════════════════════════" -ForegroundColor White

    if ($copied -gt 0) {
        Write-OK "$copied folder(s) installed successfully"
    }

    if ($skipped -gt 0) {
        Write-Warn "$skipped folder(s) not found in source"
    }

    Write-Host ""
    Write-Host "  Source:      $Repo ($Branch)" -ForegroundColor White
    Write-Host "  Destination: $destDir" -ForegroundColor White
    Write-Host "  Folders:     $($Folders -join ', ')" -ForegroundColor White
    Write-Host ""
    Write-Host "════════════════════════════════════════════════════════" -ForegroundColor White
}
finally {
    # ── Cleanup ───────────────────────────────────────────────────
    if (Test-Path $tmpDir) {
        Remove-Item -Path $tmpDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
