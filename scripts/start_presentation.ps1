param([switch]$Install)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$root = (Get-Location).Path
$python = Join-Path $root '.venv-service\Scripts\python.exe'
if ($Install) {
    if (!(Test-Path $python)) { py -3.12 -m venv .venv-service; if ($LASTEXITCODE) { throw 'Python environment creation failed' } }
    & $python -m pip install -r requirements-service.lock.txt
    if ($LASTEXITCODE) { throw 'Python dependency installation failed' }
    Push-Location firebase
    try { npm.cmd ci; if ($LASTEXITCODE) { throw 'Firebase dependency installation failed' } } finally { Pop-Location }
}
if (!(Test-Path $python)) { throw 'Run this script once with -Install.' }
if (!(Test-Path 'firebase\node_modules\.bin\firebase.cmd')) { throw 'Run this script once with -Install.' }
foreach ($port in 8000,9099,8080,9199,4000) {
    if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
        throw "Port $port is already in use. Close previous demo services or identify the conflicting process; do not stop unrelated services."
    }
}
Remove-Item Env:FIREBASE_ADMIN_CREDENTIALS_JSON -ErrorAction SilentlyContinue
Remove-Item Env:GOOGLE_APPLICATION_CREDENTIALS -ErrorAction SilentlyContinue
$env:APP_ENV = 'emulator'
$env:FIREBASE_PROJECT_ID = 'demo-strathmore-lost-found'
$env:FIREBASE_AUTH_EMULATOR_HOST = '127.0.0.1:9099'
$env:FIRESTORE_EMULATOR_HOST = '127.0.0.1:8080'
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
function Start-DemoService($name) {
    $entry = Join-Path $root 'scripts\start_local.ps1'
    Start-Process powershell.exe -WorkingDirectory $root -ArgumentList "-NoExit -ExecutionPolicy Bypass -File `"$entry`" -Service $name"
}
function Wait-Port($port, $seconds) {
    $deadline = (Get-Date).AddSeconds($seconds)
    do {
        $connection = New-Object System.Net.Sockets.TcpClient
        try { $connection.Connect('127.0.0.1', $port); return } catch { Start-Sleep -Seconds 2 } finally { $connection.Dispose() }
    } while ((Get-Date) -lt $deadline)
    throw "Port $port did not become ready. Inspect the service window."
}
Start-DemoService emulators
foreach ($port in 9099,8080,9199) { Wait-Port $port 120 }
Start-DemoService api
Wait-Port 8000 90
$health = Invoke-RestMethod 'http://127.0.0.1:8000/health' -TimeoutSec 10
if ($health.matching -ne 'separate durable worker') { throw 'Wrong API: use service.api:app, not the preview.' }
& $python -m scripts.seed_emulator
if ($LASTEXITCODE) { throw 'Demo account setup failed.' }
Start-DemoService worker
& $python -m scripts.prepare_local_demo
if ($LASTEXITCODE) { throw 'Demo verification failed; see API/worker/emulator windows.' }
Write-Host 'Local API and matching smoke test passed. Keep the three service windows running.' -ForegroundColor Green
Write-Host 'Android Studio emulator: build with -PdemoFirebase=true. See docs/LOCAL_PRESENTATION.md.'
