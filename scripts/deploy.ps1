$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $root 'backend'
$frontendDir = Join-Path $root 'frontend'

Write-Host 'Pulling latest changes...'
git -C $root pull origin main

Write-Host 'Ensuring Python environment exists...'
if (-not (Test-Path (Join-Path $backendDir '.venv'))) {
  py -3.11 -m venv (Join-Path $backendDir '.venv')
}

$python = Join-Path $backendDir '.venv/Scripts/python.exe'

Write-Host 'Installing backend dependencies...'
& $python -m pip install --upgrade pip
& $python -m pip install -r (Join-Path $backendDir 'requirements.txt')

Write-Host 'Installing frontend dependencies...'
Set-Location $frontendDir
npm install

Write-Host 'Restarting backend and frontend...'
$backendProcess = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess -ErrorAction SilentlyContinue
if ($backendProcess) {
  Stop-Process -Id $backendProcess -Force -ErrorAction SilentlyContinue
}

$frontendProcess = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess -ErrorAction SilentlyContinue
if ($frontendProcess) {
  Stop-Process -Id $frontendProcess -Force -ErrorAction SilentlyContinue
}

Start-Job -Name 'pte-backend' -ScriptBlock {
  Set-Location $using:backendDir
  $env:KMP_DUPLICATE_LIB_OK = 'TRUE'
  & "$using:backendDir/.venv/Scripts/python.exe" -m uvicorn server:app --host 0.0.0.0 --port 8000
} | Out-Null

Start-Job -Name 'pte-frontend' -ScriptBlock {
  Set-Location $using:frontendDir
  $env:PORT = '3000'
  $env:HOST = '0.0.0.0'
  npm run dev -- --hostname 0.0.0.0 --port 3000
} | Out-Null

Write-Host 'Deployment complete.'
