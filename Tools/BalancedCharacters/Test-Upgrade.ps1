# 0.2.2 upgrade tool: uses the old launcher scripts, kept in Tools\BalancedCharacters\Legacy.
param([string]$PackageDirectory = 'F:\ChatGPT\Balanced-Characters-0.2.2')
$ErrorActionPreference = 'Stop'
$installed = 'G:\Game\yugioh online\copy of master dual\Yu-Gi-Oh!  Master Duel\YgoMaster-BalancedCharacters'
$fixtureRoot = Join-Path 'F:\ChatGPT' ('BalancedUpgrade022Test-' + [Guid]::NewGuid().ToString('N'))
function New-Fixture([string]$Name) {
    $game = Join-Path $fixtureRoot $Name
    $runtime = Join-Path $game 'YgoMaster-BalancedCharacters'
    New-Item -ItemType Directory -Path (Join-Path $game 'LocalData') -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $game 'masterduel.exe') -Value 'validation fixture only'
    foreach ($dir in @('Data\ClientData','Data\Players\Sentinel')) { New-Item -ItemType Directory -Path (Join-Path $runtime $dir) -Force | Out-Null }
    foreach ($name in @('YgoMaster.exe','YgoMasterClient.exe','YgoMasterLoader.dll','Start-Balanced.ps1','Start-Balanced.cmd','Stop-Balanced.ps1','Open-Balanced-Settings.cmd','Data\Settings.json','Data\ClientData\ClientSettings.json')) {
        Copy-Item -LiteralPath (Join-Path $installed $name) -Destination (Join-Path $runtime $name)
    }
    Copy-Item -LiteralPath (Join-Path $installed 'Data\BalancedCharacters') -Destination (Join-Path $runtime 'Data\BalancedCharacters') -Recurse
    New-Item -ItemType Directory -Path (Join-Path $runtime 'Data\ClientData\IDS') -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $installed 'Data\ClientData\IDS\IDS_BALANCED_CHARACTERS.txt') -Destination (Join-Path $runtime 'Data\ClientData\IDS\IDS_BALANCED_CHARACTERS.txt')
    $modePath = Join-Path $runtime 'Data\BalancedCharacters\Mode.json'
    $mode = Get-Content -LiteralPath $modePath -Raw | ConvertFrom-Json
    $mode.enabled = $false
    $mode | Add-Member -NotePropertyName PreserveUnknown -NotePropertyValue 'sentinel'
    $mode | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $modePath -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $runtime 'Data\Players\Sentinel\save.txt') -Value 'personal-save-sentinel'
    return $runtime
}
function Hashes([string]$Runtime) {
    $result = @{}
    foreach ($file in Get-ChildItem -LiteralPath $Runtime -Recurse -File) {
        if ($file.FullName -like '*\UpgradeBackups\*') { continue }
        $result[$file.FullName.Substring($Runtime.Length+1)] = (Get-FileHash -LiteralPath $file.FullName).Hash
    }
    return $result
}
function Assert-Original([string]$Runtime, $Expected) {
    foreach ($name in $Expected.Keys) {
        if ((Get-FileHash -LiteralPath (Join-Path $Runtime $name)).Hash -ne $Expected[$name]) { throw "Changed original file: $name" }
    }
}
$runtime = New-Fixture 'success'
$old = Hashes $runtime
& (Join-Path $PackageDirectory 'Upgrade.ps1') -TargetDirectory $runtime -DryRun
Assert-Original $runtime $old
& (Join-Path $PackageDirectory 'Upgrade.ps1') -TargetDirectory $runtime
$mode = Get-Content -LiteralPath (Join-Path $runtime 'Data\BalancedCharacters\Mode.json') -Raw | ConvertFrom-Json
if ($mode.enabled -ne $false -or $mode.PreserveUnknown -ne 'sentinel' -or $mode.activeCharacterIds.Count -ne 14) { throw 'Mode preference/roster mismatch' }
foreach ($name in @('Data\Settings.json','Data\ClientData\ClientSettings.json','Data\Players\Sentinel\save.txt','YgoMasterClient.exe','Data\BalancedCharacters\Decks\source-v1\kaiba.json','Data\BalancedCharacters\Decks\source-v1\joey.json')) {
    if ((Get-FileHash -LiteralPath (Join-Path $runtime $name)).Hash -ne $old[$name]) { throw "User data changed: $name" }
}
& (Join-Path $PackageDirectory 'Upgrade.ps1') -TargetDirectory $runtime
$backup = @(Get-ChildItem -LiteralPath (Join-Path $runtime 'UpgradeBackups') -Directory)
if ($backup.Count -ne 1) { throw 'Repeat install created extra backup' }
& (Join-Path $PackageDirectory 'Restore.ps1') -TargetDirectory $runtime -BackupDirectory $backup[0].FullName
Assert-Original $runtime $old
Write-Output 'PASS dry run, install, repeat, disabled/unknown preferences, settings/saves/client/decks preserved, manual restore'
$runtime = New-Fixture 'rollback'
$old = Hashes $runtime
$modePath = Join-Path $runtime 'Data\BalancedCharacters\Mode.json'
(Get-Item -LiteralPath $modePath).IsReadOnly = $true
$failed = $false
try { & (Join-Path $PackageDirectory 'Upgrade.ps1') -TargetDirectory $runtime } catch { $failed = $true; Write-Output "Expected failure: $($_.Exception.Message)" }
if (-not $failed) { throw 'Expected write failure was not raised' }
(Get-Item -LiteralPath $modePath).IsReadOnly = $false
Assert-Original $runtime $old
$files = Hashes $runtime
if ($files.Count -ne $old.Count) { throw 'Rollback retained new payload files' }
Write-Output 'PASS forced late write failure restores every original file and removes new payload files'
Write-Output "Fixture evidence: $fixtureRoot (not playable game copies)"
