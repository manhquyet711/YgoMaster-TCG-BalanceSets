param([string]$TargetDirectory = 'G:\Game\yugioh online\copy of master dual\Yu-Gi-Oh!  Master Duel\YgoMaster-BalancedCharacters', [switch]$DryRun)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($TargetDirectory).TrimEnd('\')
$payload = Join-Path $PSScriptRoot 'Payload'
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'manifest.json') -Raw | ConvertFrom-Json
$modeRelative = 'Data\BalancedCharacters\Mode.json'
$modePath = Join-Path $root $modeRelative
$mode = Get-Content -LiteralPath $modePath -Raw | ConvertFrom-Json
if ($mode.schemaVersion -ne 1 -or $mode.activeDeckRevision -ne 'source-v1') { throw 'Unsupported balanced mode schema/revision.' }
if ((Get-FileHash -LiteralPath (Join-Path $root 'YgoMasterClient.exe')).Hash -ne $manifest.expectedClientSha256) { throw 'Client differs from the inspected working 0.2.1 installation.' }
$already = $mode.contentVersion -eq $manifest.contentVersion
if (-not $already -and $mode.contentVersion -ne $manifest.fromContentVersion) { throw 'This package upgrades the existing 0.2.1 balanced mod.' }
$newMode = Get-Content -LiteralPath (Join-Path $payload $modeRelative) -Raw | ConvertFrom-Json
foreach ($entry in $manifest.files) {
    foreach ($base in @($payload, $root)) {
        $path = [IO.Path]::GetFullPath((Join-Path $base $entry.path))
        if (-not $path.StartsWith(([IO.Path]::GetFullPath($base).TrimEnd('\') + '\'), [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe package path.' }
    }
    if ((Get-FileHash -LiteralPath (Join-Path $payload $entry.path)).Hash -ne $entry.sha256) { throw "Damaged payload: $($entry.path)" }
    if ($entry.path -eq $modeRelative) { continue }
    $dest = Join-Path $root $entry.path
    if ($already) {
        if (-not (Test-Path -LiteralPath $dest) -or (Get-FileHash -LiteralPath $dest).Hash -ne $entry.sha256) { throw "Installed file changed: $($entry.path)" }
    } elseif ($entry.previousSha256 -and (Test-Path -LiteralPath $dest)) {
        if ((Get-FileHash -LiteralPath $dest).Hash -ne $entry.previousSha256) { throw "Existing file differs from inspected 0.2.1: $($entry.path). No files changed." }
    } elseif (-not $entry.previousSha256 -and (Test-Path -LiteralPath $dest) -and $entry.path -like 'Data\BalancedCharacters\*') {
        throw "New roster file already exists: $($entry.path). Preserve it for review."
    }
}
$assemblyPath = Join-Path (Split-Path -Parent $root) 'GameAssembly.dll'
if ((Test-Path -LiteralPath $assemblyPath) -and (Get-FileHash -LiteralPath $assemblyPath).Hash -ne $manifest.gameAssemblySha256) { throw 'Game binary differs from inspected 2.8.0.' }
if ($already) {
    if ((($mode.activeCharacterIds | Sort-Object) -join ',') -ne (($newMode.activeCharacterIds | Sort-Object) -join ',')) { throw 'Installed roster selection changed; preserve it for review.' }
    Write-Output '0.2.2 already installed and verified.'; return
}
if ((($mode.activeCharacterIds | Sort-Object) -join ',') -ne 'joey,kaiba') { throw 'Expected the original Kaiba/Joey runtime.' }
& (Join-Path $payload 'Start-Balanced.ps1') -RuntimeDirectory $root -ValidateOnly
if ($DryRun) { Write-Output 'PASS 0.2.2 upgrade: 14 characters / 182 matchups; backups; settings and saves preserved.'; return }
if (Get-Process -Name masterduel,BalancedSettingsEditor,SettingsEditor -ErrorAction SilentlyContinue) { throw 'Close Master Duel and settings editors, then run Install.cmd again.' }
$serverPath = Join-Path $root 'YgoMaster.exe'
foreach ($process in @(Get-Process -Name YgoMaster -ErrorAction SilentlyContinue | Where-Object Path -EQ $serverPath)) {
    Stop-Process -Id $process.Id
    if (-not $process.WaitForExit(5000)) { throw 'Balanced server did not stop.' }
}
$backup = Join-Path $root ('UpgradeBackups\0.2.2-' + [DateTime]::Now.ToString('yyyyMMdd-HHmmss-fff'))
New-Item -ItemType Directory -Path (Join-Path $backup 'Data\BalancedCharacters') -Force | Out-Null
Copy-Item -LiteralPath $modePath -Destination (Join-Path $backup $modeRelative)
$replaced = @(); $created = @()
try {
    foreach ($entry in $manifest.files) {
        if ($entry.path -eq $modeRelative) { continue }
        $dest = Join-Path $root $entry.path
        if (Test-Path -LiteralPath $dest) {
            $saved = Join-Path $backup $entry.path
            New-Item -ItemType Directory -Path (Split-Path -Parent $saved) -Force | Out-Null
            Copy-Item -LiteralPath $dest -Destination $saved
            $replaced += [string]$entry.path
        } else { $created += [string]$entry.path }
        New-Item -ItemType Directory -Path (Split-Path -Parent $dest) -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $payload $entry.path) -Destination $dest -Force
        if ((Get-FileHash -LiteralPath $dest).Hash -ne $entry.sha256) { throw "Installed file checksum mismatch: $($entry.path)" }
    }
    $mode.contentVersion = $newMode.contentVersion
    $mode.activeCharacterIds = $newMode.activeCharacterIds
    $mode.note = $newMode.note
    $mode | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $modePath -Encoding UTF8
    $verify = Get-Content -LiteralPath $modePath -Raw | ConvertFrom-Json
    if ($verify.contentVersion -ne $manifest.contentVersion -or $verify.activeCharacterIds.Count -ne 14) { throw 'Mode update failed.' }
    & (Join-Path $root 'Start-Balanced.ps1') -RuntimeDirectory $root -ValidateOnly
} catch {
    Copy-Item -LiteralPath (Join-Path $backup $modeRelative) -Destination $modePath -Force
    foreach ($name in $replaced) { Copy-Item -LiteralPath (Join-Path $backup $name) -Destination (Join-Path $root $name) -Force }
    foreach ($name in $created) { $dest = Join-Path $root $name; if (Test-Path -LiteralPath $dest) { Remove-Item -LiteralPath $dest } }
    throw
}
Write-Output "Installed 0.2.2. Backups: $backup"
Write-Output 'Run Start-Balanced.cmd, then Stories. Fourteen Balanced Characters gates are available.'
Write-Output 'Each battle is selectable immediately. Goal unlocks after beating every opponent in that gate.'
