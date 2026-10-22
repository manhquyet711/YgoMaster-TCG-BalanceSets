$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
if (-not (Test-Path -LiteralPath (Join-Path $root 'YgoMaster.exe'))) { $root = Join-Path $root 'YgoMaster' }
$serverPath = Join-Path $root 'YgoMaster.exe'
Get-Process -Name YgoMaster -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $serverPath } | Stop-Process
Write-Host 'Stopped this installation of the Balanced Characters server.'
