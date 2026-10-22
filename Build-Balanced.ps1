param([switch]$CompilePrototype)
$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    & python -m unittest discover -s Tools/BalancedCharacters -p 'test_*.py' -v
    if ($LASTEXITCODE -ne 0) { throw 'Content tests failed.' }
    & '.\Tools\BalancedCharacters\Resolve-CardMap.ps1'
    if ($CompilePrototype) { & '.\Tools\BalancedCharacters\Build-Content.ps1' }
    & '.\Build-Updated.ps1' -Validate
    & '.\Tools\BalancedCharacters\SettingsEditor\Build-Editor.ps1' -OutputPath (Join-Path $PSScriptRoot 'YgoMaster\BalancedSettingsEditor.exe')
    $csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
    & $csc '/nologo' '/out:Tools\BalancedCharacters\ValidateBalancedCharacters.exe' 'Tools\BalancedCharacters\ValidateBalancedCharacters.cs'
    if ($LASTEXITCODE -ne 0) { throw 'Policy validator compile failed.' }
    & '.\Tools\BalancedCharacters\ValidateBalancedCharacters.exe' '.\YgoMaster'
    if ($LASTEXITCODE -ne 0) { throw 'Compiled policy tests failed.' }
    & $csc '/nologo' '/out:Tools\BalancedCharacters\ValidateBalancedIntegration.exe' 'Tools\BalancedCharacters\ValidateBalancedIntegration.cs'
    if ($LASTEXITCODE -ne 0) { throw 'Integration test compilation failed.' }
    & '.\Tools\BalancedCharacters\ValidateBalancedIntegration.exe' '.\YgoMaster'
    if ($LASTEXITCODE -ne 0) { throw 'Handler integration checks failed.' }
    Write-Host 'Server integration checks passed. In-game acceptance remains pending.'
} finally { Pop-Location }
