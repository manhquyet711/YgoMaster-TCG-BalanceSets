param(
    [string]$GameDirectory = 'G:\Game\yugioh online\copy of master dual\Yu-Gi-Oh!  Master Duel',
    [switch]$VerifyOnly
)
$ErrorActionPreference = 'Stop'
$gameRoot = (Resolve-Path -LiteralPath $GameDirectory).Path.TrimEnd('\')
$sourceRoot = Join-Path $gameRoot 'YgoMaster-TCG-release20250630'
$runtimeRoot = Join-Path $gameRoot 'YgoMaster-TCG-Updated-2.8.0'
if (-not (Test-Path -LiteralPath (Join-Path $gameRoot 'masterduel.exe'))) { throw 'masterduel.exe was not found.' }
if (-not (Test-Path -LiteralPath (Join-Path $sourceRoot 'YgoMaster.sln'))) { throw 'The original TCG source project was not found.' }
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'manifest.json') -Raw | ConvertFrom-Json
$payloadRoot = Join-Path $PSScriptRoot 'Payload'
function Safe-Child([string]$Root, [string]$Relative) {
    $result = [IO.Path]::GetFullPath((Join-Path $Root $Relative))
    if (-not $result.StartsWith($Root.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid package path.' }
    return $result
}
# Complete all hash checks before copying any files.
foreach ($entry in $manifest.Files) {
    $payload = Safe-Child $payloadRoot $entry.Path
    if ((Get-FileHash -LiteralPath $payload -Algorithm SHA256).Hash -ne $entry.NewHash) { throw "Package checksum mismatch: $($entry.Path)" }
    $target = Safe-Child $sourceRoot $entry.Path
    if (Test-Path -LiteralPath $target) {
        $hash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
        if ($hash -ne $entry.OldHash -and $hash -ne $entry.NewHash) { throw "Source changed since this update was prepared: $($entry.Path). No files updated." }
    } elseif ($entry.OldHash) {
        throw "Original file is missing: $($entry.Path). No files updated."
    }
}
Write-Host "Verified $($manifest.Files.Count) update files and original source checksums."
if ($VerifyOnly) { return }
if (Test-Path -LiteralPath $runtimeRoot) { throw "The new runtime folder already exists: $runtimeRoot. No files updated." }
$backupRoot = Join-Path $gameRoot ('TCG-Source-Backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
if (Test-Path -LiteralPath $backupRoot) { throw 'Backup folder already exists. Please retry in a few seconds.' }
foreach ($entry in $manifest.Files) {
    $target = Safe-Child $sourceRoot $entry.Path
    if (Test-Path -LiteralPath $target) {
        $backup = Safe-Child $backupRoot $entry.Path
        New-Item -ItemType Directory -Path (Split-Path -Parent $backup) -Force | Out-Null
        Copy-Item -LiteralPath $target -Destination $backup
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
    Copy-Item -LiteralPath (Safe-Child $payloadRoot $entry.Path) -Destination $target -Force
}
New-Item -ItemType Directory -Path $runtimeRoot | Out-Null
$sourceRuntime = Join-Path $sourceRoot 'YgoMaster'
foreach ($file in Get-ChildItem -LiteralPath $sourceRuntime -Recurse -File) {
    $relative = $file.FullName.Substring($sourceRuntime.Length + 1)
    if ($relative -match '^Data[\\/](Players|Decks)([\\/]|$)' -or $file.Extension -in '.cpp', '.rc', '.res', '.hpp', '.pdb') { continue }
    $target = Safe-Child $runtimeRoot $relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
    Copy-Item -LiteralPath $file.FullName -Destination $target
}
Write-Host "Updated source: $sourceRoot"
Write-Host "Backups: $backupRoot"
Write-Host "Run: $(Join-Path $runtimeRoot 'YgoMasterClient.exe')"
Write-Host 'Player saves were not migrated. Test a new campaign first.'
