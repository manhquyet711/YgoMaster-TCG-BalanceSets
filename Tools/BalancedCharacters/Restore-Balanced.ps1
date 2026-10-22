param([Parameter(Mandatory=$true)][string]$BackupDirectory,
    [string]$TargetDirectory = 'G:\Game\yugioh online\copy of master dual\Yu-Gi-Oh!  Master Duel\YgoMaster-BalancedCharacters')
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($TargetDirectory).TrimEnd('\')
$backup = [IO.Path]::GetFullPath($BackupDirectory).TrimEnd('\')
if (-not $backup.StartsWith(($root + '\UpgradeBackups\0.2.2-'), [StringComparison]::OrdinalIgnoreCase) -or
    -not (Test-Path -LiteralPath (Join-Path $backup 'Data\BalancedCharacters\Mode.json'))) { throw 'Select a 0.2.2 upgrade backup inside this runtime.' }
if (Get-Process -Name masterduel,BalancedSettingsEditor,SettingsEditor -ErrorAction SilentlyContinue) { throw 'Close Master Duel and settings editors before restoring.' }
$serverPath = Join-Path $root 'YgoMaster.exe'
foreach ($process in @(Get-Process -Name YgoMaster -ErrorAction SilentlyContinue | Where-Object Path -EQ $serverPath)) {
    Stop-Process -Id $process.Id
    if (-not $process.WaitForExit(5000)) { throw 'Balanced server did not stop.' }
}
foreach ($file in Get-ChildItem -LiteralPath $backup -Recurse -File) {
    $relative = $file.FullName.Substring($backup.Length+1)
    $dest = [IO.Path]::GetFullPath((Join-Path $root $relative))
    if (-not $dest.StartsWith(($root + '\'), [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe backup path.' }
    New-Item -ItemType Directory -Path (Split-Path -Parent $dest) -Force | Out-Null
    Copy-Item -LiteralPath $file.FullName -Destination $dest -Force
}
Write-Output 'Restored pre-upgrade files. Settings, saves and run logs were preserved.'
