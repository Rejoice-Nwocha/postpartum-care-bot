param(
    [string]$AppUrl = "http://127.0.0.1:10000"
)

$ErrorActionPreference = "Stop"

Write-Host "Care Sister smoke test" -ForegroundColor Cyan
Write-Host "App: $AppUrl"

try {
    $root = Invoke-RestMethod -Uri "$AppUrl/" -Method Get -TimeoutSec 10
    Write-Host "[PASS] GET /" -ForegroundColor Green
    $root | ConvertTo-Json -Depth 5
}
catch {
    Write-Host "[FAIL] GET /" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

try {
    $diagnostics = Invoke-RestMethod -Uri "$AppUrl/diagnostics" -Method Get -TimeoutSec 10
    Write-Host "[PASS] GET /diagnostics" -ForegroundColor Green
    $diagnostics | ConvertTo-Json -Depth 5
}
catch {
    Write-Host "[FAIL] GET /diagnostics" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

Write-Host "Smoke test complete." -ForegroundColor Green
