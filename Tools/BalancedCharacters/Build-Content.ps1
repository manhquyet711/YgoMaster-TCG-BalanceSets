$ErrorActionPreference = 'Stop'
& python (Join-Path $PSScriptRoot 'content.py') compile
if ($LASTEXITCODE -ne 0) { throw 'Content build blocked; resolve the reported deck prerequisite.' }
