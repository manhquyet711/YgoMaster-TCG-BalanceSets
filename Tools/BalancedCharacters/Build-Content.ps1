$ErrorActionPreference = 'Stop'
& python (Join-Path $PSScriptRoot 'content.py') compile
if ($LASTEXITCODE -ne 0) { throw 'Content build blocked; resolve the reported deck prerequisite.' }
# Deck set packs for the Balanced Settings Editor's "Deck set" list (Revisions/<revision>)
& python (Join-Path $PSScriptRoot 'content.py') packs
if ($LASTEXITCODE -ne 0) { throw 'Deck set packs could not be built.' }
