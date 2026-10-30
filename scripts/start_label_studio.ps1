$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskLauncher = Join-Path $taskRoot '.venv-label-studio\Scripts\label-studio.exe'
if (-not (Test-Path -LiteralPath $taskLauncher)) {
    throw 'Brak Label Studio w srodowisku projektu.'
}
$env:LABEL_STUDIO_BASE_DATA_DIR = Join-Path $taskRoot '.label-studio'
$env:LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED = 'true'
$env:LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT = Join-Path $taskRoot 'data\raw\images'
$env:LABEL_STUDIO_DISABLE_TELEMETRY = 'true'
$env:PYTHONUTF8 = '1'
& $taskLauncher start --port 8080 --internal-host 127.0.0.1
