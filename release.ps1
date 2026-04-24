param(
    [string]$Repo = "alimtvnetwork/coding-guidelines-v15"
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
$requiredPaths = @("spec", "linters", "linter-scripts", "install.sh", "install.ps1", "install-config.json", "README.md")

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
    Copy-Item -Path (Join-Path $PSScriptRoot "README.md") -Destination (Join-Path $stagingDir "README.md") -Force
}

function New-ReleaseArchives {
    $zipPath = Join-Path $distDir "$releaseName.zip"
    $tarPath = Join-Path $distDir "$releaseName.tar.gz"

    if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
    if (Test-Path $tarPath) { Remove-Item $tarPath -Force }

    Compress-Archive -Path $stagingDir -DestinationPath $zipPath -CompressionLevel Optimal
    tar -C $distDir -czf $tarPath $releaseName
}

function New-Checksums {
    $zipPath = Join-Path $distDir "$releaseName.zip"
    $tarPath = Join-Path $distDir "$releaseName.tar.gz"
    $zipHash = (Get-FileHash -Path $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $tarHash = (Get-FileHash -Path $tarPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $content = @(
        "$zipHash  $releaseName.zip",
        "$tarHash  $releaseName.tar.gz"
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
