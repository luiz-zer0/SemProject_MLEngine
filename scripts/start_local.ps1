param(
    [ValidateSet('api','worker','emulators','seed')][string]$Service = 'api',
    [string]$Python = '.\.venv-service\Scripts\python.exe'
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:APP_ENV = 'emulator'
$env:FIREBASE_PROJECT_ID = 'demo-strathmore-lost-found'
$env:FIREBASE_AUTH_EMULATOR_HOST = '127.0.0.1:9099'
$env:FIRESTORE_EMULATOR_HOST = '127.0.0.1:8080'
if ($Service -eq 'emulators') {
    if (-not (Get-Command java -ErrorAction SilentlyContinue)) {
        $studioJava = 'C:\Program Files\Android\Android Studio\jbr'
        if (Test-Path "$studioJava\bin\java.exe") {
            $env:JAVA_HOME = $studioJava
            $env:Path = "$studioJava\bin;$env:Path"
        }
    }
    Push-Location firebase
    try { npx.cmd firebase-tools emulators:start --project demo-strathmore-lost-found } finally { Pop-Location }
} elseif ($Service -eq 'api') {
    & $Python -m uvicorn service.api:app --host 127.0.0.1 --port 8000
} elseif ($Service -eq 'worker') {
    & $Python -m service.worker
} else {
    & $Python -m scripts.seed_emulator
}
