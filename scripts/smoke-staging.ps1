$ErrorActionPreference = "Stop"

$baseUrl = $env:REALMEET_BASE_URL
if ([string]::IsNullOrWhiteSpace($baseUrl)) {
    $baseUrl = "http://localhost:18000"
}
$baseUrl = $baseUrl.TrimEnd("/")

Write-Host "Checking $baseUrl/health"
$health = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get -TimeoutSec 10
if ($health.status -ne "ok") {
    throw "Unexpected /health status: $($health.status)"
}

Write-Host "Checking $baseUrl/ready"
$ready = Invoke-RestMethod -Uri "$baseUrl/ready" -Method Get -TimeoutSec 10
if ($ready.status -ne "ready") {
    throw "Unexpected /ready status: $($ready.status)"
}

Write-Host "Smoke checks passed for $baseUrl"
