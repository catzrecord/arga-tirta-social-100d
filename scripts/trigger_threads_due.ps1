$ErrorActionPreference = 'Stop'

$repo = 'catzrecord/arga-tirta-social-100d'
$workflow = 'arga-tirta-threads.yml'
$gh = (Get-Command gh -ErrorAction SilentlyContinue).Source
if (-not $gh) {
    $gh = 'C:\Program Files\GitHub CLI\gh.exe'
}

$logDir = Join-Path $env:LOCALAPPDATA 'ArgaTirtaThreads'
$logFile = Join-Path $logDir 'scheduler.log'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

for ($attempt = 1; $attempt -le 5; $attempt++) {
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'
    "[$timestamp] Dispatch attempt $attempt" | Add-Content -LiteralPath $logFile

    $output = & $gh workflow run $workflow --repo $repo -f mode=due -f force_token_refresh=false 2>&1
    $exitCode = $LASTEXITCODE
    $output | ForEach-Object { "  $_" } | Add-Content -LiteralPath $logFile

    if ($exitCode -eq 0) {
        "[$timestamp] Dispatch accepted" | Add-Content -LiteralPath $logFile
        exit 0
    }

    if ($attempt -lt 5) {
        Start-Sleep -Seconds 30
    }
}

throw 'Threads workflow dispatch failed after 5 attempts.'
