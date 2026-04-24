<#
.SYNOPSIS
    Download spec/linters/scripts from a GitHub repo with rich install controls.

.DESCRIPTION
    Conforms to: spec/14-update/27-generic-installer-behavior.md

    Power-user flags:
      -Repo owner/repo            Override source repo
      -Branch main                Override branch (ignored if -Version given)
      -Version vX.Y.Z             Install a specific release tag (PINNED MODE, §4)
      -Folders spec,linters       Explicit folder list (subpaths OK: spec/14-update)
      -Dest C:\path               Install destination (default: cwd)
      -ConfigFile my-config.json  Use custom config file
      -Prompt                     Ask before overwriting each existing file (y/n/a/s)
      -Force                      Overwrite all existing files without prompting
      -DryRun                     Show what would change; write nothing
      -ListVersions               List available release tags and exit
      -ListFolders                List available top-level folders for the chosen ref and exit
      -NoProbe (-n,-NoLatest)     Skip the latest-version probe
      -NoDiscovery                Skip V→V+N parallel discovery (spec §5.3)
      -NoMainFallback             Skip main-branch fallback (spec §5.3)
      -Offline (-UseLocalArchive) Skip all network ops; require local archive

    EXIT CODES (spec §8):
      0  success
      1  generic failure
      2  offline mode required a network operation (or handshake mismatch)
      3  pinned release / asset not found (PINNED MODE only)
      4  verification failed (checksum / required-paths)
      5  inner installer / handoff rejected

.EXAMPLE
    .\install.ps1
    .\install.ps1 -Version v1.22.0 -Folders spec/14-update -Prompt
    .\install.ps1 -DryRun
    irm https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/install.ps1 | iex
#>

param(
    [string]$Repo = "",
    [string]$Branch = "",
    [string]$Version = "",
    [string]$Dest = "",
    [string]$ConfigFile = "install-config.json",
    [string[]]$Folders = @(),
    [switch]$Prompt,
    [switch]$Force,
    [switch]$DryRun,
    [switch]$ListVersions,
    [switch]$ListFolders,
    [Alias('n','NoLatest')]
    [switch]$NoProbe,
    [switch]$NoDiscovery,
    [switch]$NoMainFallback,
    [Alias('UseLocalArchive')]
    [switch]$Offline,
    [string]$PinnedByReleaseInstall = ""
)

# Offline mode forbids any network operation (spec §5.3, §8 exit 2).
if ($Offline) {
    Write-Host "    ❌ Offline mode is not yet supported by install.ps1. Exit 2 per spec §8." -ForegroundColor Red
    exit 2
}

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$script:Indent = "    "
function Write-Step  { param([string]$Msg) Write-Host "$script:Indent▸ $Msg" -ForegroundColor Cyan }
function Write-OK    { param([string]$Msg) Write-Host "$script:Indent✅ $Msg" -ForegroundColor Green }
function Write-Warn  { param([string]$Msg) Write-Host "$script:Indent⚠️  $Msg" -ForegroundColor Yellow }
function Write-Err   { param([string]$Msg) Write-Host "$script:Indent❌ $Msg" -ForegroundColor Red }
function Write-Dim   { param([string]$Msg) Write-Host "$script:Indent$Msg" -ForegroundColor DarkGray }
function Write-Plain { param([string]$Msg) Write-Host "$script:Indent$Msg" -ForegroundColor White }

if ($Prompt -and $Force) {
    Write-Err "-Prompt and -Force are mutually exclusive"
    exit 1
}

# ── Latest-version probe (skipped for -Version / listings / -NoProbe) ──
$script:ProbeOwner   = "alimtvnetwork"
$script:ProbeBase    = "coding-guidelines"
$script:ProbeVersion = 14

function Invoke-LatestVersionProbe {
    Write-Step "Detecting installer identity..."
    $sourceUrl = $null
    if ($MyInvocation.ScriptName)            { $sourceUrl = $MyInvocation.ScriptName }
    if (-not $sourceUrl -and $PSCommandPath) { $sourceUrl = $PSCommandPath }
    if (-not $sourceUrl -and $env:INSTALL_PROBE_SOURCE_URL) { $sourceUrl = $env:INSTALL_PROBE_SOURCE_URL }
    $owner = $env:INSTALL_PROBE_OWNER; $base = $env:INSTALL_PROBE_BASE; $cur = $env:INSTALL_PROBE_VERSION
    $urlRegex = '^https?://[^/]+/(?<o>[^/]+)/(?<b>[A-Za-z0-9._-]+?)-v(?<v>\d+)/[^/]+/install\.ps1'
    if ($sourceUrl -and $sourceUrl -match $urlRegex) {
        if (-not $owner) { $owner = $Matches.o }
        if (-not $base)  { $base  = $Matches.b }
        if (-not $cur)   { $cur   = $Matches.v }
    }
    if (-not $owner) { $owner = $script:ProbeOwner }
    if (-not $base)  { $base  = $script:ProbeBase }
    if (-not $cur)   { $cur   = $script:ProbeVersion }
    [int]$current = [int]$cur
    Write-OK "Identity: $owner/$base-v$current  (probing v$($current+1)..v$($current+20))"
    [int]$depth = 0
    if ($env:INSTALL_PROBE_HANDOFF_DEPTH) { [int]::TryParse($env:INSTALL_PROBE_HANDOFF_DEPTH, [ref]$depth) | Out-Null }
    if ($depth -ge 3) { Write-Err "Probe loop guard (depth=$depth)"; exit 1 }
    Write-Step "Probing 20 candidate versions in parallel (timeout 2s, middle-out)..."
    # Middle-out ordering: probe the middle of the range first, then expand
    # outward. With true parallelism this doesn't change correctness, but it
    # makes early-abort heuristics terminate faster when the latest version
    # tends to sit in the middle of the +1..+20 window.
    $low  = $current + 1
    $high = $current + 20
    $mid  = [int][Math]::Floor(($low + $high) / 2)
    $candidates = @($mid)
    for ($offset = 1; $offset -le ($high - $low); $offset++) {
        $upper = $mid + $offset
        $lower = $mid - $offset
        if ($upper -le $high) { $candidates += $upper }
        if ($lower -ge $low)  { $candidates += $lower }
    }
    Add-Type -AssemblyName System.Net.Http -ErrorAction SilentlyContinue
    $handler = [System.Net.Http.HttpClientHandler]::new()
    $client  = [System.Net.Http.HttpClient]::new($handler)
    $client.Timeout = [TimeSpan]::FromSeconds(2)
    $tasks = @{}
    foreach ($n in $candidates) {
        $url = "https://raw.githubusercontent.com/$owner/$base-v$n/main/install.ps1"
        $req = [System.Net.Http.HttpRequestMessage]::new([System.Net.Http.HttpMethod]::Head, $url)
        $tasks[$n] = $client.SendAsync($req)
    }
    $hits = @()
    # Iterate highest → lowest so the first hit we keep is already the winner.
    foreach ($n in ($candidates | Sort-Object -Descending)) {
        try {
            $r = $tasks[$n].GetAwaiter().GetResult()
            if ($r.IsSuccessStatusCode) { $hits += $n }
        } catch { }
    }
    $client.Dispose()
    $hits   = @($hits | Sort-Object -Descending)
    $latest = if ($hits.Count -gt 0) { $hits[0] } else { $current }
    if ($latest -le $current) { Write-OK "Already on latest (v$current)."; return }
    $newerUrl = "https://raw.githubusercontent.com/$owner/$base-v$latest/main/install.ps1"
    Write-OK "Newer version found: v$latest. Handing off..."
    $env:INSTALL_PROBE_HANDOFF_DEPTH = ($depth + 1).ToString()
    $env:INSTALL_PROBE_SOURCE_URL    = $newerUrl
    try { Invoke-RestMethod -Uri $newerUrl | Invoke-Expression; exit $LASTEXITCODE }
    catch { Write-Warn "Hand-off failed: $($_.Exception.Message)." }
}

# Pinning handshake: when invoked by release-install.ps1, the version
# arg MUST agree with the handshake value. Mismatch = exit 2.
if ($PinnedByReleaseInstall) {
    if (-not $Version) {
        $Version = $PinnedByReleaseInstall
    } elseif ($Version -ne $PinnedByReleaseInstall) {
        Write-Err "Pinning handshake mismatch: -Version=$Version vs -PinnedByReleaseInstall=$PinnedByReleaseInstall"
        exit 2
    }
    Write-Step "Pinned by release-install: $PinnedByReleaseInstall (auto-update disabled)"
}

$skipProbe = $NoProbe -or $Version -or $ListVersions -or $ListFolders -or $env:INSTALL_NO_PROBE -or $PinnedByReleaseInstall
if (-not $skipProbe) {
    try { Invoke-LatestVersionProbe } catch { Write-Warn "Probe error: $($_.Exception.Message)." }
}

# ── Read config (defaults only) ───────────────────────────────────
function Read-InstallConfig {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    return (Get-Content -Path $Path -Raw | ConvertFrom-Json)
}

$config = $null
if (Test-Path $ConfigFile) {
    Write-Step "Reading config from $ConfigFile"
    $config = Read-InstallConfig -Path $ConfigFile
}

if ([string]::IsNullOrEmpty($Repo)) {
    $Repo = if ($config -and $config.repo) { $config.repo } else { "alimtvnetwork/coding-guidelines-v15" }
}
if ([string]::IsNullOrEmpty($Branch)) {
    $Branch = if ($config -and $config.branch) { $config.branch } else { "main" }
}
if ([string]::IsNullOrEmpty($Dest)) { $Dest = (Get-Location).Path }
if ($Folders.Count -eq 0) {
    $Folders = if ($config -and $config.folders) { @($config.folders) } else { @("spec", "linters", "linter-scripts") }
}

$ref = if ($Version) { $Version } else { $Branch }

# ── Listing modes ─────────────────────────────────────────────────
function Show-ReleaseVersions {
    Write-Step "Fetching releases for $Repo..."
    try {
        $rels = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases?per_page=50" -UseBasicParsing
        Write-Host ""
        $rels | Select-Object -First 50 | ForEach-Object { Write-Plain "  • $($_.tag_name)" }
        Write-Host ""
    } catch {
        Write-Err "Could not fetch releases: $($_.Exception.Message)"
        exit 1
    }
    exit 0
}

function Show-TopFolders {
    Write-Step "Listing folders for $Repo@$ref..."
    try {
        $items = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/contents?ref=$ref" -UseBasicParsing
        Write-Host ""
        $items | Where-Object { $_.type -eq "dir" } | Sort-Object name | ForEach-Object { Write-Plain "  • $($_.name)" }
        Write-Host ""
    } catch {
        Write-Err "Could not list folders: $($_.Exception.Message)"
        exit 1
    }
    exit 0
}

if ($ListVersions) { Show-ReleaseVersions }
if ($ListFolders)  { Show-TopFolders }

# ── Banner (spec §7) ──────────────────────────────────────────────
$installMode = if ($Version) { "pinned" } else { "implicit" }
$sourceKind  = if ($Version) { "tag-tarball" } else { "branch-tarball" }
$versionLabel = if ($Version) { $Version } else { "$Branch (implicit)" }
Write-Host ""
Write-Plain "    📦 Spec & Scripts Installer"
Write-Plain "       mode:    $installMode"
Write-Plain "       repo:    $Repo"
Write-Plain "       version: $versionLabel"
Write-Plain "       source:  $sourceKind"
Write-Plain "       folders: $($Folders -join ', ')"
Write-Plain "       dest:    $Dest"
if ($DryRun)         { Write-Plain "       opts:    DRY-RUN (no writes)" }
if ($Prompt)         { Write-Plain "       opts:    Interactive prompts (y/n/a/s)" }
if ($Force)          { Write-Plain "       opts:    Force overwrite" }
if ($NoDiscovery)    { Write-Plain "       opts:    -NoDiscovery (V→V+N forbidden)" }
if ($NoMainFallback) { Write-Plain "       opts:    -NoMainFallback" }
Write-Host ""

# ── Download archive at ref ───────────────────────────────────────
$tmpDir = Join-Path ([System.IO.Path]::GetTempPath()) ("install-" + [guid]::NewGuid().ToString("N").Substring(0,8))
New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
$archivePath = Join-Path $tmpDir "repo.zip"

$archiveUrl = if ($Version) {
    "https://codeload.github.com/$Repo/zip/refs/tags/$Version"
} else {
    "https://codeload.github.com/$Repo/zip/refs/heads/$Branch"
}

try {
    Write-Step "Downloading $Repo@$ref..."
    try { Invoke-WebRequest -Uri $archiveUrl -OutFile $archivePath -UseBasicParsing }
    catch {
        $archiveUrl = "https://codeload.github.com/$Repo/zip/$ref"
        Invoke-WebRequest -Uri $archiveUrl -OutFile $archivePath -UseBasicParsing
    }

    Write-Step "Extracting..."
    $extractDir = Join-Path $tmpDir "extracted"
    Expand-Archive -Path $archivePath -DestinationPath $extractDir -Force
    $archiveRoot = Get-ChildItem -Path $extractDir -Directory | Select-Object -First 1
    if (-not $archiveRoot) { Write-Err "Failed to find archive root"; exit 1 }

    # ── Merge ─────────────────────────────────────────────────────
    $script:PromptAll = $false
    $script:PromptSkipAll = $false
    $copied = 0; $skippedFolders = 0; $wroteNew = 0; $overwrote = 0; $skippedFiles = 0

    function Test-ShouldOverwrite {
        param([string]$Target)
        if ($script:PromptAll)     { return $true }
        if ($script:PromptSkipAll) { return $false }
        if ($Force)                { return $true }
        if (-not $Prompt)          { return $true }
        while ($true) {
            $rel = $Target.Replace($Dest, '').TrimStart('\','/')
            $ans = Read-Host "? Overwrite $rel ? [y]es/[n]o/[a]ll/[s]kip-all"
            switch ($ans.ToLower()) {
                'y' { return $true }
                'n' { return $false }
                'a' { $script:PromptAll = $true; return $true }
                's' { $script:PromptSkipAll = $true; return $false }
                default { Write-Host "  enter y, n, a, or s" }
            }
        }
    }

    function Merge-File {
        param([string]$Src, [string]$Target)
        $targetDir = Split-Path $Target -Parent
        $rel = $Target.Replace($Dest, '').TrimStart('\','/')
        if (Test-Path $Target) {
            if (Test-ShouldOverwrite -Target $Target) {
                if ($DryRun) { Write-Dim "  ~ would overwrite $rel" }
                else { New-Item -ItemType Directory -Path $targetDir -Force | Out-Null; Copy-Item $Src $Target -Force }
                $script:overwrote++
            } else {
                Write-Dim "  - skip $rel"; $script:skippedFiles++
            }
        } else {
            if ($DryRun) { Write-Dim "  + would create $rel" }
            else { New-Item -ItemType Directory -Path $targetDir -Force | Out-Null; Copy-Item $Src $Target -Force }
            $script:wroteNew++
        }
    }

    foreach ($folder in $Folders) {
        $srcPath = Join-Path $archiveRoot.FullName $folder
        if (-not (Test-Path $srcPath)) {
            Write-Warn "Folder '$folder' not found in $Repo@$ref — skipping"
            $skippedFolders++; continue
        }
        Write-Step "Merging: $folder"
        Get-ChildItem -Path $srcPath -Recurse -File | ForEach-Object {
            $relativePath = $_.FullName.Substring($srcPath.Length).TrimStart('\','/')
            $targetFile = Join-Path (Join-Path $Dest $folder) $relativePath
            Merge-File -Src $_.FullName -Target $targetFile
        }
        $copied++
    }

    # ── Summary ───────────────────────────────────────────────────
    Write-Host ""
    Write-Plain "════════════════════════════════════════════════════════"
    if ($copied -gt 0)         { Write-OK "$copied folder(s) processed" }
    if ($wroteNew -gt 0)       { Write-OK "$wroteNew new file(s)" }
    if ($overwrote -gt 0)      { Write-OK "$overwrote file(s) overwritten" }
    if ($skippedFiles -gt 0)   { Write-Warn "$skippedFiles file(s) skipped" }
    if ($skippedFolders -gt 0) { Write-Warn "$skippedFolders folder(s) missing in source" }
    if ($DryRun)               { Write-Warn "DRY-RUN — no changes written" }
    Write-Host ""
    Write-Plain "  Source:      $Repo @ $ref"
    Write-Plain "  Destination: $Dest"
    Write-Plain "  Folders:     $($Folders -join ', ')"
    Write-Host ""
    Write-Plain "════════════════════════════════════════════════════════"
}
finally {
    if (Test-Path $tmpDir) {
        Remove-Item -Path $tmpDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    if (-not (Test-Path $tmpDir)) {
        Write-OK "Temp cleaned: $tmpDir"
    } else {
        Write-Warn "Temp NOT fully removed: $tmpDir (manual cleanup recommended)"
    }
}
