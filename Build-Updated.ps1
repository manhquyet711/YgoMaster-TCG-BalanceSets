param([switch]$Validate)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
$msbuild = $null
if (Test-Path -LiteralPath $vswhere) {
    $msbuild = & $vswhere -latest -products '*' -find 'MSBuild\**\Bin\MSBuild.exe' | Select-Object -First 1
}
if (-not $msbuild) { $msbuild = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\MSBuild.exe' }
& $msbuild 'YgoMaster.sln' '/p:Configuration=Release' '/p:Platform=x64' '/nologo' '/verbosity:minimal'
if ($LASTEXITCODE -ne 0) { throw 'C# build failed.' }
if (-not (Test-Path -LiteralPath 'YgoMaster\YgoMasterLoader.dll')) {
    throw 'YgoMasterLoader.dll is missing. Restore the bundled official v1.79 loader or compile YgoMasterLoader.cpp using Visual C++.'
}
Write-Host 'Built client and server for Master Duel 2.8.0. Using the unchanged official v1.79 native loader.'
if ($Validate) {
    $csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
    & $csc '/nologo' '/out:Tools\ValidateCampaign.exe' 'Tools\ValidateCampaign.cs'
    if ($LASTEXITCODE -ne 0) { throw 'Validation tool compilation failed.' }
    & '.\Tools\ValidateCampaign.exe' '.\YgoMaster'
    if ($LASTEXITCODE -ne 0) { throw 'Campaign validation failed.' }
}
