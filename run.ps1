<#
.SYNOPSIS
    Root-level convenience runner. Dispatches to lint or slides sub-commands.

.DESCRIPTION
    Sub-commands (positional first arg):
      (none)        → lint  (legacy default — git pull + Go validator on src/)
      lint          → same as no-args, but explicit
      slides        → git pull → build slides-app/ → preview → open in browser
      help          → print this table

    Spec: spec/15-distribution-and-runner/02-runner-contract.md

.EXAMPLE
    .\run.ps1
    .\run.ps1 lint -Path cmd -MaxLines 20
    .\run.ps1 slides
    .\run.ps1 help
#>

param(
    [Parameter(Position = 0)]
    [string]$Command = "",

    [string]$Path = "src",
    [switch]$Json,
    [int]$MaxLines = 15,
    [switch]$d
)

$ErrorActionPreference = "Stop"

function Show-Help {
    Write-Host ""
    Write-Host "  coding-guidelines-v17 — root runner" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Usage: .\run.ps1 [<command>] [<flags>]"
    Write-Host ""
    Write-Host "  Commands:"
    Write-Host "    (none)   git pull + run Go validator on src/   (legacy default)"
    Write-Host "    lint     same as no-args, but explicit"
    Write-Host "    slides   build & preview slides-app/, open browser"
    Write-Host "    help     this table"
    Write-Host ""
    Write-Host "  Lint flags forwarded to linter-scripts/run.ps1:"
    Write-Host "    -Path <dir>      Directory to scan (default: src)"
    Write-Host "    -MaxLines <n>    Max function body lines (default: 15)"
    Write-Host "    -Json            JSON output"
    Write-Host "    -d               Skip validation, only git pull"
    Write-Host ""
}

function Invoke-Lint {
    $inner = Join-Path $PSScriptRoot "linter-scripts" "run.ps1"
    if (-not (Test-Path $inner)) {
        Write-Host "❌ Cannot find $inner" -ForegroundColor Red
        exit 1
    }
    $splat = @{ Path = $Path; MaxLines = $MaxLines }
    if ($Json) { $splat["Json"] = $true }
    if ($d)    { $splat["d"]    = $true }
    & $inner @splat
    exit $LASTEXITCODE
}

function Test-Command {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Invoke-Slides {
    Write-Host ""
    Write-Host "▸ slides — building offline deck and opening in browser" -ForegroundColor Cyan
    Write-Host ""

    $slidesDir = Join-Path $PSScriptRoot "slides-app"
    if (-not (Test-Path $slidesDir)) {
        Write-Host "❌ slides-app/ not found at $slidesDir" -ForegroundColor Red
        Write-Host "   See spec-slides/00-overview.md for the slides spec." -ForegroundColor Yellow
        exit 1
    }

    Write-Host "▸ git pull (best effort)..." -ForegroundColor Cyan
    try { git pull | Out-Host } catch { Write-Host "⚠️  git pull failed — continuing with local state" -ForegroundColor Yellow }

    $runner = $null
    if (Test-Command "bun")  { $runner = "bun" }
    elseif (Test-Command "pnpm") { $runner = "pnpm" }
    else {
        Write-Host "❌ Need 'bun' or 'pnpm' on PATH to build slides-app." -ForegroundColor Red
        Write-Host "   Install bun:  irm bun.sh/install.ps1 | iex" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "▸ using package runner: $runner" -ForegroundColor Cyan

    Push-Location $slidesDir
    try {
        Write-Host "▸ install dependencies..." -ForegroundColor Cyan
        & $runner install
        if ($LASTEXITCODE -ne 0) { Write-Host "❌ install failed" -ForegroundColor Red; exit 1 }

        Write-Host "▸ build..." -ForegroundColor Cyan
        & $runner run build
        if ($LASTEXITCODE -ne 0) { Write-Host "❌ build failed" -ForegroundColor Red; exit 1 }

        Write-Host "▸ start preview server (background)..." -ForegroundColor Cyan
        $preview = Start-Process -FilePath $runner -ArgumentList @("run", "preview") -PassThru -NoNewWindow

        $url = "http://localhost:4173/"
        $ready = $false
        for ($i = 0; $i -lt 20; $i++) {
            Start-Sleep -Milliseconds 500
            try {
                $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop
                if ($r.StatusCode -lt 500) { $ready = $true; break }
            } catch { }
        }
        if (-not $ready) {
            Write-Host "⚠️  preview not reachable at $url — opening browser anyway" -ForegroundColor Yellow
        }

        Write-Host "▸ opening $url" -ForegroundColor Cyan
        Start-Process $url

        Write-Host ""
        Write-Host "▸ slides — preview running. Press Ctrl-C to stop." -ForegroundColor Green
        Write-Host ""
        Wait-Process -Id $preview.Id
    }
    finally {
        Pop-Location
    }
}

switch ($Command.ToLower()) {
    ""        { Invoke-Lint }
    "lint"    { Invoke-Lint }
    "slides"  { Invoke-Slides }
    "help"    { Show-Help; exit 0 }
    "-h"      { Show-Help; exit 0 }
    "--help"  { Show-Help; exit 0 }
    "-?"      { Show-Help; exit 0 }
    default   {
        if ($Command.StartsWith("-")) {
            # Treat as a lint flag — re-route through lint with $Command as -Path-style fallback
            Invoke-Lint
        } else {
            Write-Host "❌ Unknown command: $Command" -ForegroundColor Red
            Show-Help
            exit 2
        }
    }
}
