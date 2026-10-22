param([string]$OutputPath = (Join-Path $PSScriptRoot 'BalancedSettingsEditor.exe'))
$ErrorActionPreference = 'Stop'
$csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
& $csc /nologo /target:winexe /platform:x64 /reference:System.Windows.Forms.dll /reference:System.Drawing.dll /reference:System.Web.Extensions.dll ("/out:" + $OutputPath) (Join-Path $PSScriptRoot 'BalancedSettingsEditor.cs')
if ($LASTEXITCODE -ne 0) { throw 'Editor compilation failed.' }
