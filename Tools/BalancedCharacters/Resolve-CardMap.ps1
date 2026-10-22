$ErrorActionPreference = 'Stop'
& python (Join-Path $PSScriptRoot 'content.py') resolve
if ($LASTEXITCODE -ne 0) { throw 'Card mapping failed. See CARD-AUDIT.json.' }
