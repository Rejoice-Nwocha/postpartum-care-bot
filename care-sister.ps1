param(
    [Parameter(Position = 0)]
    [ValidateSet("help", "status", "test", "diagnostics", "logs", "evolution-status")]
    [string]$Command = "help",

    [string]$AppUrl = "http://127.0.0.1:10000"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

function Write-Section([string]$Title) {
    Write-Host "`n=== $Title ===" -ForegroundColor Cyan
}

function Show-Help {
    Write-Host @"
Care Sister CLI

Usage:
  .\care-sister.ps1 <command>

Commands:
  help                Show this help
  status              Show Git branch/status and project files
  test                Run the Python test suite
  diagnostics        Check the local Care Sister FastAPI diagnostics endpoint
  logs                Show recent Docker/Evolution logs
  evolution-status    Show local Evolution API container status

Examples:
  .\care-sister.ps1 status
  .\care-sister.ps1 test
  .\care-sister.ps1 diagnostics
  .\care-sister.ps1 evolution-status
  .\care-sister.ps1 logs

Safety:
  - This CLI does not print .env contents, API keys, WhatsApp sessions, or credentials.
  - It does not send WhatsApp messages by itself.
  - Run it from the Care Sister project directory.
"@
}

function Invoke-Git([string[]]$GitArgs) {
    & git @GitArgs
    if ($LASTEXITCODE -ne 0) {
        throw "git command failed with exit code $LASTEXITCODE"
    }
}

function Test-PythonSuite {
    Write-Section "Python tests"

    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        throw "Python was not found on PATH. Activate your project environment first."
    }

    $pytest = Get-Command pytest -ErrorAction SilentlyContinue
    if ($null -eq $pytest) {
        Write-Host "pytest is not installed in the current environment." -ForegroundColor Yellow
        Write-Host "Install the development test dependency with: python -m pip install pytest" -ForegroundColor Yellow
        exit 2
    }

    & pytest -q
    if ($LASTEXITCODE -ne 0) {
        throw "Test suite failed with exit code $LASTEXITCODE"
    }
}

function Get-AppDiagnostics {
    Write-Section "Care Sister diagnostics"
    try {
        $result = Invoke-RestMethod -Uri "$AppUrl/diagnostics" -Method Get -TimeoutSec 10
        $result | ConvertTo-Json -Depth 5
    }
    catch {
        Write-Host "Could not reach $AppUrl/diagnostics" -ForegroundColor Yellow
        Write-Host $_.Exception.Message -ForegroundColor Yellow
        exit 1
    }
}

function Get-DockerLogs {
    Write-Section "Recent Evolution logs"

    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker CLI was not found on PATH."
    }

    $containers = docker ps --format "{{.Names}}"
    if ($LASTEXITCODE -ne 0) {
        throw "Docker is not available. Start Docker Desktop and try again."
    }

    $evolution = $containers | Where-Object { $_ -match "evolution" }
    if (-not $evolution) {
        Write-Host "No running container with 'evolution' in its name was found." -ForegroundColor Yellow
        Write-Host "Running containers:" -ForegroundColor DarkGray
        docker ps --format "table {{.Names}}\t{{.Status}}"
        return
    }

    foreach ($container in $evolution) {
        Write-Host "`n--- $container ---" -ForegroundColor Green
        docker logs --tail 80 $container 2>&1
    }
}

switch ($Command) {
    "help" {
        Show-Help
    }

    "status" {
        Write-Section "Git status"
        Invoke-Git @("branch", "--show-current")
        Invoke-Git @("status", "--short", "--branch")

        Write-Section "Recent commits"
        Invoke-Git @("log", "-5", "--oneline", "--decorate")

        Write-Section "Project files"
        Get-ChildItem -Force | Select-Object Mode, Length, LastWriteTime, Name | Format-Table -AutoSize
    }

    "test" {
        Test-PythonSuite
    }

    "diagnostics" {
        Get-AppDiagnostics
    }

    "logs" {
        Get-DockerLogs
    }

    "evolution-status" {
        Write-Section "Evolution API container status"

        if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
            throw "Docker CLI was not found on PATH."
        }

        docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | Select-String -Pattern "NAME|evolution|NAMES"
    }
}
