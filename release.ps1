param(
    [string]$Repo = "alimtvnetwork/coding-guidelines-v17"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Write-Step { param([string]$Msg) Write-Host "▸ $Msg" -ForegroundColor Cyan }
function Write-OK { param([string]$Msg) Write-Host "✅ $Msg" -ForegroundColor Green }
function Write-Err { param([string]$Msg) Write-Host "❌ $Msg" -ForegroundColor Red }

$packageJson = Get-Content -Path (Join-Path $PSScriptRoot "package.json") -Raw | ConvertFrom-Json
$version = $packageJson.version
$distDir = Join-Path $PSScriptRoot "release-artifacts"
$releaseName = "coding-guidelines-v$version"
$stagingDir = Join-Path $distDir $releaseName
$requiredPaths = @("spec", "linters", "linter-scripts", "install.sh", "install.ps1", "install-config.json", "readme.md", "release-install.sh", "release-install.ps1")

function Test-RequiredPaths {
    $isMissing = $false

    foreach ($path in $requiredPaths) {
        if (Test-Path (Join-Path $PSScriptRoot $path)) {
            continue
        }

        Write-Err "Missing required path: $path"
        $isMissing = $true
    }

    if ($isMissing) {
        exit 1
    }
}

function Initialize-Staging {
    if (Test-Path $stagingDir) {
        Remove-Item -Path $stagingDir -Recurse -Force
    }

    New-Item -ItemType Directory -Path $stagingDir -Force | Out-Null
}

function Copy-ReleaseFiles {
    Copy-Item -Path (Join-Path $PSScriptRoot "spec") -Destination (Join-Path $stagingDir "spec") -Recurse -Force
    Copy-Item -Path (Join-Path $PSScriptRoot "linters") -Destination (Join-Path $stagingDir "linters") -Recurse -Force
    Copy-Item -Path (Join-Path $PSScriptRoot "linter-scripts") -Destination (Join-Path $stagingDir "linter-scripts") -Recurse -Force
    Copy-Item -Path (Join-Path $PSScriptRoot "install.sh") -Destination (Join-Path $stagingDir "install.sh") -Force
    Copy-Item -Path (Join-Path $PSScriptRoot "install.ps1") -Destination (Join-Path $stagingDir "install.ps1") -Force
    Copy-Item -Path (Join-Path $PSScriptRoot "install-config.json") -Destination (Join-Path $stagingDir "install-config.json") -Force
    Copy-Item -Path (Join-Path $PSScriptRoot "readme.md") -Destination (Join-Path $stagingDir "readme.md") -Force
}

function New-ReleaseArchives {
    $zipPath = Join-Path $distDir "$releaseName.zip"
    $tarPath = Join-Path $distDir "$releaseName.tar.gz"

    if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
    if (Test-Path $tarPath) { Remove-Item $tarPath -Force }

    Compress-Archive -Path $stagingDir -DestinationPath $zipPath -CompressionLevel Optimal
    tar -C $distDir -czf $tarPath $releaseName
}

function Invoke-BakeReleaseInstallers {
    # Spec: spec/14-update/25-release-pinned-installer.md §Release-Time Build Step
    # Substitute __VERSION_PLACEHOLDER__ with the resolved tag (prefixed
    # with `v`) and write standalone copies into $distDir for upload as
    # release assets.
    $tag    = "v$version"
    $srcSh  = Join-Path $PSScriptRoot "release-install.sh"
    $srcPs1 = Join-Path $PSScriptRoot "release-install.ps1"
    $outSh  = Join-Path $distDir "release-install.sh"
    $outPs1 = Join-Path $distDir "release-install.ps1"

    if (-not (Test-Path $srcSh) -or -not (Test-Path $srcPs1)) {
        Write-Err "Canonical release-install scripts missing at repo root"
        exit 1
    }

    (Get-Content $srcSh  -Raw).Replace("__VERSION_PLACEHOLDER__", $tag) | Set-Content -Path $outSh  -NoNewline
    (Get-Content $srcPs1 -Raw).Replace("__VERSION_PLACEHOLDER__", $tag) | Set-Content -Path $outPs1 -NoNewline

    if ((Get-Content $outSh -Raw)  -match '__VERSION_PLACEHOLDER__' -or `
        (Get-Content $outPs1 -Raw) -match '__VERSION_PLACEHOLDER__') {
        Write-Err "Baking failed — placeholder still present in baked installers"
        exit 1
    }
    if ((Get-Content $outSh  -Raw) -notmatch [regex]::Escape("BAKED_VERSION=`"$tag`""))    { Write-Err "release-install.sh did not bake to $tag";  exit 1 }
    if ((Get-Content $outPs1 -Raw) -notmatch [regex]::Escape("BakedVersion = `"$tag`""))   { Write-Err "release-install.ps1 did not bake to $tag"; exit 1 }
}

function New-Checksums {
    $zipPath = Join-Path $distDir "$releaseName.zip"
    $tarPath = Join-Path $distDir "$releaseName.tar.gz"
    $bakedSh  = Join-Path $distDir "release-install.sh"
    $bakedPs1 = Join-Path $distDir "release-install.ps1"
    $zipHash = (Get-FileHash -Path $zipPath  -Algorithm SHA256).Hash.ToLowerInvariant()
    $tarHash = (Get-FileHash -Path $tarPath  -Algorithm SHA256).Hash.ToLowerInvariant()
    $shHash  = (Get-FileHash -Path $bakedSh  -Algorithm SHA256).Hash.ToLowerInvariant()
    $psHash  = (Get-FileHash -Path $bakedPs1 -Algorithm SHA256).Hash.ToLowerInvariant()
    $content = @(
        "$zipHash  $releaseName.zip",
        "$tarHash  $releaseName.tar.gz",
        "$shHash  release-install.sh",
        "$psHash  release-install.ps1"
    )

    Set-Content -Path (Join-Path $distDir "checksums.txt") -Value $content
}

Write-Step "Validating required files"
Test-RequiredPaths
Write-Step "Preparing release staging directory"
Initialize-Staging
Write-Step "Copying release files"
Copy-ReleaseFiles
Write-Step "Creating archives"
New-ReleaseArchives
Write-Step "Baking release-install.{sh,ps1} with VERSION_PLACEHOLDER -> v$version"
Invoke-BakeReleaseInstallers
Write-Step "Generating checksums"
New-Checksums
Write-OK "Release artifacts created"
Write-Host ""
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor White
Write-Host "  Coding Guidelines Release Pack" -ForegroundColor White
Write-Host "  Version:     v$version" -ForegroundColor White
Write-Host "  Repo:        $Repo" -ForegroundColor White
Write-Host "  Output:      $distDir" -ForegroundColor White
Write-Host "  Raw PS URL:  https://raw.githubusercontent.com/$Repo/main/install.ps1" -ForegroundColor White
Write-Host "  Raw SH URL:  https://raw.githubusercontent.com/$Repo/main/install.sh" -ForegroundColor White
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor White
Write-Host ""
Write-Host "  Pinned one-liners (paste into the GitHub Release body):" -ForegroundColor Yellow
Write-Host ""
Write-Host "  PowerShell:" -ForegroundColor White
Write-Host "    irm https://github.com/$Repo/releases/download/v$version/release-install.ps1 | iex" -ForegroundColor Gray
Write-Host ""
Write-Host "  Bash:" -ForegroundColor White
Write-Host "    curl -fsSL https://github.com/$Repo/releases/download/v$version/release-install.sh | bash" -ForegroundColor Gray
Write-Host ""
Write-Host "  Upload these assets to the v$version release:" -ForegroundColor White
Write-Host "    - $releaseName.zip"            -ForegroundColor Gray
Write-Host "    - $releaseName.tar.gz"         -ForegroundColor Gray
Write-Host "    - release-install.sh         (baked, pinned to v$version)" -ForegroundColor Gray
Write-Host "    - release-install.ps1        (baked, pinned to v$version)" -ForegroundColor Gray
Write-Host "    - checksums.txt"               -ForegroundColor Gray
