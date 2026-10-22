param([string]$InstalledRuntime = 'G:\Game\yugioh online\copy of master dual\Yu-Gi-Oh!  Master Duel\YgoMaster-BalancedCharacters', [string]$OutputDirectory = 'F:\ChatGPT\Balanced-Characters-0.2.2')
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$out = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $out) { throw 'Preserve the existing release and choose a new output directory.' }
$payload = Join-Path $out 'Payload'
New-Item -ItemType Directory -Path $payload -Force | Out-Null
# The installed 0.2.1 client already implements thumbnails and the native map.
# This milestone updates server/content; it does not replace that working client.
foreach ($name in @('YgoMaster.exe')) {
    Copy-Item -LiteralPath (Join-Path $root "YgoMaster\$name") -Destination (Join-Path $payload $name)
}
foreach ($name in @('Start-Balanced.ps1','Start-Balanced.cmd','Stop-Balanced.ps1','Open-Balanced-Settings.cmd')) {
    Copy-Item -LiteralPath (Join-Path $root $name) -Destination (Join-Path $payload $name)
}
foreach ($file in Get-ChildItem -LiteralPath (Join-Path $root 'YgoMaster\Data\BalancedCharacters') -Recurse -File) {
    $rel = $file.FullName.Substring((Join-Path $root 'YgoMaster').Length+1)
    if ($rel -match '\\Logs\\') { continue }
    $dest = Join-Path $payload $rel
    New-Item -ItemType Directory -Path (Split-Path -Parent $dest) -Force | Out-Null
    Copy-Item -LiteralPath $file.FullName -Destination $dest
}
$ids = 'Data\ClientData\IDS\IDS_BALANCED_CHARACTERS.txt'
New-Item -ItemType Directory -Path (Split-Path -Parent (Join-Path $payload $ids)) -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $root "YgoMaster\$ids") -Destination (Join-Path $payload $ids)
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Upgrade-Balanced.ps1') -Destination (Join-Path $out 'Upgrade.ps1')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Restore-Balanced.ps1') -Destination (Join-Path $out 'Restore.ps1')
Copy-Item -LiteralPath (Join-Path $root 'Docs\BalancedCharacters\RELEASE-0.2.2.md') -Destination (Join-Path $out 'README.md')
$extensions = @('.cs','.csproj','.sln','.ps1','.py','.cmd','.bat','.md','.json','.csv','.txt','.log','.config','.resx','.props','.targets','.ico')
foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File) {
    $rel = $file.FullName.Substring($root.Length+1)
    if ($rel -match '(^|\\)(\.git|obj|bin|Dist|__pycache__|Logs)(\\|$)') { continue }
    $scope = $rel -match '^YgoMasterServer\\|^YgoMasterClient\\|^Docs\\|^Tools\\|^YgoMaster\\Data\\BalancedCharacters\\' -or $rel -notmatch '\\'
    if ($scope -and ($file.Extension -in $extensions -or $rel -eq 'LICENSE')) {
        $dest = Join-Path $out "Source\$rel"
        New-Item -ItemType Directory -Path (Split-Path -Parent $dest) -Force | Out-Null
        Copy-Item -LiteralPath $file.FullName -Destination $dest
    }
}
$files = @(Get-ChildItem -LiteralPath $payload -Recurse -File | Sort-Object FullName | ForEach-Object {
    $rel = $_.FullName.Substring($payload.Length+1)
    $old = Join-Path $InstalledRuntime $rel
    $previous = if (Test-Path -LiteralPath $old) { (Get-FileHash -LiteralPath $old).Hash } else { $null }
    # Permit the launcher fix or a local wrapper; the old launcher is backed up.
    if ($rel -eq 'Start-Balanced.ps1') { $previous = $null }
    [ordered]@{path=$rel;bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash;previousSha256=$previous}
})
[ordered]@{schemaVersion=1;version='0.2.2';contentVersion='0.2.2-prototype';fromContentVersion='0.2.1-prototype';runtimeTested=$false;
    expectedClientSha256=(Get-FileHash -LiteralPath (Join-Path $InstalledRuntime 'YgoMasterClient.exe')).Hash;
    gameAssemblySha256='CA24A284A86DC394F6B0CBEAAD455D29E5F6B95FC8DB8FC42812B29DE3C7620C';files=$files} |
    ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding UTF8
@'
@echo off
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Upgrade.ps1"
if errorlevel 1 (echo Installation failed. & pause & exit /b 1)
pause
'@ | Set-Content -LiteralPath (Join-Path $out 'Install.cmd') -Encoding ASCII
Write-Output "Prepared release folder: $out"
Write-Output 'Run dry-run and fixture install tests, then compress the validated folder.'
