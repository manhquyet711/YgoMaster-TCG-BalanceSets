param([string]$Version = '0.2.2')
$ErrorActionPreference = 'Stop'
if ($Version -notmatch '^\d+\.\d+\.\d+$') { throw 'Use a numeric semantic package version.' }
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$out = Join-Path $root ('Dist\Balanced-Characters-' + $Version)
if (Test-Path -LiteralPath $out) { throw 'Package folder exists; preserve it and choose a new package version before rebuilding.' }
$payload = Join-Path $out 'Payload'
New-Item -ItemType Directory -Path $payload -Force | Out-Null
foreach ($name in @('YgoMaster.exe','YgoMasterClient.exe','YgoMasterLoader.dll','YgoMaster.exe.config','YgoMasterClient.exe.config','Start Game.exe')) {
    $source = Join-Path $root "YgoMaster\$name"
    if (Test-Path -LiteralPath $source) { Copy-Item -LiteralPath $source -Destination (Join-Path $payload $name) }
}
# Start Game.exe is the launcher (settings + start); Stop-Balanced.ps1 stays as a hidden helper.
foreach ($name in @('Stop-Balanced.ps1')) {
    Copy-Item -LiteralPath (Join-Path $root $name) -Destination (Join-Path $payload $name)
}
foreach ($relative in @('Data\Settings.json','Data\ClientData\ClientSettings.json','Data\ClientData\IDS\IDS_BALANCED_CHARACTERS.txt')) {
    $dest = Join-Path $payload $relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $dest) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $root "YgoMaster\$relative") -Destination $dest
}
Copy-Item -LiteralPath (Join-Path $root 'YgoMaster\Data\BalancedCharacters') -Destination (Join-Path $payload 'Data\BalancedCharacters') -Recurse
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Install-Prototype.ps1') -Destination (Join-Path $out 'Install-Prototype.ps1')
Copy-Item -LiteralPath (Join-Path $root 'Docs\BalancedCharacters\INSTALL.md') -Destination (Join-Path $out 'README.md')
$sourceSnapshot = Join-Path $out 'Source'
$extensions = @('.cs','.cpp','.h','.hpp','.csproj','.sln','.ps1','.py','.cmd','.bat','.md','.json','.csv','.txt','.log','.config','.resx','.rc','.props','.targets','.ico')
foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File) {
    $relative = $file.FullName.Substring($root.Length+1)
    if ($relative -match '(^|\\)(\.git|obj|bin|Dist|__pycache__)(\\|$)') { continue }
    $scope = $relative -match '^YgoMasterServer\\|^YgoMasterClient\\|^YgoMasterLoader\\|^YgoMasterFiddler\\|^Docs\\|^Tools\\|^YgoMaster\\Data\\BalancedCharacters\\' -or $relative -notmatch '\\'
    if ($scope -and ($file.Extension -in $extensions -or $relative -eq 'LICENSE')) {
        $dest = Join-Path $sourceSnapshot $relative
        New-Item -ItemType Directory -Path (Split-Path -Parent $dest) -Force | Out-Null
        Copy-Item -LiteralPath $file.FullName -Destination $dest
    }
}
$files = @(Get-ChildItem -LiteralPath $payload -Recurse -File | Sort-Object FullName | ForEach-Object {
    [ordered]@{path=$_.FullName.Substring($payload.Length+1);bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash}
})
$baseline = Get-Content -LiteralPath (Join-Path $root 'Docs\BalancedCharacters\BASELINE.json') -Raw | ConvertFrom-Json
$gameAssembly = $baseline.files | Where-Object { [IO.Path]::GetFileName($_.path) -eq 'GameAssembly.dll' }
[ordered]@{schemaVersion=1;version=$Version;runtimeTested=$false;gameAssemblySha256=$gameAssembly.sha256;files=$files} |
    ConvertTo-Json -Depth 7 | Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8
@'
@echo off
cd /d "%~dp0"
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-Prototype.ps1"
if errorlevel 1 (echo Installation failed. & pause & exit /b 1)
pause
'@ | Set-Content -LiteralPath (Join-Path $out 'Install.cmd') -Encoding ascii
$zip = Join-Path $root ('Dist\Balanced-Characters-' + $Version + '.zip')
Compress-Archive -LiteralPath $out -DestinationPath $zip
Write-Host "Packaged $zip; game assets and player saves excluded."
