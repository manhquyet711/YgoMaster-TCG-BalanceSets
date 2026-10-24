param(
    [string]$GameRoot = 'G:\Game\yugioh online\copy of master dual\Yu-Gi-Oh!  Master Duel',
    [string]$BaseModFolder = 'YgoMaster-TCG-Updated-2.8.0',
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$game = [IO.Path]::GetFullPath($GameRoot)
if ($BaseModFolder -match '[/\\]' -or $BaseModFolder -eq '..') { throw 'BaseModFolder must be a folder name.' }
$baseMod = Join-Path $game $BaseModFolder
$target = Join-Path $game 'YgoMaster-BalancedCharacters'
$payload = Join-Path $PSScriptRoot 'Payload'
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'manifest.json') -Raw | ConvertFrom-Json
if (-not (Test-Path -LiteralPath (Join-Path $game 'masterduel.exe'))) { throw 'masterduel.exe not found in selected game directory.' }
if (-not (Test-Path -LiteralPath (Join-Path $game 'LocalData') -PathType Container)) { throw 'Downloaded LocalData is missing.' }
if ((Get-FileHash -LiteralPath (Join-Path $game 'GameAssembly.dll')).Hash -ne $manifest.gameAssemblySha256) { throw 'GameAssembly differs from the inspected 2.8.0 game. Revalidate compatibility before installation.' }
if (-not (Test-Path -LiteralPath (Join-Path $baseMod 'Data\Solo.json'))) { throw 'Updated base TCG mod is missing.' }
$baseSettings = Get-Content -LiteralPath (Join-Path $baseMod 'Data\ClientData\ClientSettings.json') -Raw
if ($baseSettings -notmatch '"SupportedGameVersion"\s*:\s*"2\.8\.0"') { throw 'The base mod is not configured for game 2.8.0.' }
if (Test-Path -LiteralPath $target) { throw 'Target folder already exists. It may contain saves. Use the existing installation or choose a separate game copy for this initial installer.' }
foreach ($entry in $manifest.files) {
    $relative = [string]$entry.path
    $file = [IO.Path]::GetFullPath((Join-Path $payload $relative))
    $prefix = [IO.Path]::GetFullPath($payload).TrimEnd('\') + '\'
    if (-not $file.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe package path.' }
    if ((Get-FileHash -LiteralPath $file).Hash -ne $entry.sha256) { throw "Payload hash mismatch: $relative" }
}
if ($DryRun) {
    Write-Host "PASS install plan: create $target; copy base Data without players/decks; overlay validated prototype; use ports 5099/5098."
    return
}
New-Item -ItemType Directory -Path $target | Out-Null
$data = Join-Path $baseMod 'Data'
& robocopy $data (Join-Path $target 'Data') /E /XD (Join-Path $data 'Players') (Join-Path $data 'Decks') (Join-Path $data 'Logs') (Join-Path $data 'BgmDuelLogs') /XF 'Player.json' '*.dmp' /NFL /NDL /NJH /NJS /NP
if ($LASTEXITCODE -gt 7) { throw "Base data copy failed with code $LASTEXITCODE. Target is incomplete; do not launch it." }
foreach ($entry in $manifest.files) {
    $dest = Join-Path $target $entry.path
    New-Item -ItemType Directory -Path (Split-Path -Parent $dest) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $payload $entry.path) -Destination $dest -Force
    if ((Get-FileHash -LiteralPath $dest).Hash -ne $entry.sha256) { throw "Installed hash mismatch: $($entry.path)" }
}
Write-Host "Prototype installed at $target"
Write-Host 'Run Start Game.exe there and press Start Game; open SOLO > Stories > Balanced Characters.'
Write-Host 'This is a development prototype; an in-game duel has not yet been verified.'
