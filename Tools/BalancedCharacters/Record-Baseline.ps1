param([string]$GameRoot = 'G:\Game\yugioh online\copy of master dual\Yu-Gi-Oh!  Master Duel')
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$docs = Join-Path $root 'Docs\BalancedCharacters'
New-Item -ItemType Directory -Path $docs -Force | Out-Null
$paths = @((Join-Path $GameRoot 'masterduel.exe'), (Join-Path $GameRoot 'GameAssembly.dll'))
$paths += @(Get-ChildItem -LiteralPath (Join-Path $GameRoot 'masterduel_Data') -Recurse -File -ErrorAction SilentlyContinue | Where-Object Name -Match '^duel.*\.dll$' | ForEach-Object FullName)
$paths += @('YgoMaster.exe','YgoMasterClient.exe','YgoMasterLoader.dll') | ForEach-Object { Join-Path $root "YgoMaster\$_" }
$files = foreach ($path in $paths) {
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        $item = Get-Item -LiteralPath $path
        [ordered]@{path=$item.FullName; bytes=$item.Length; sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash; modifiedUtc=$item.LastWriteTimeUtc.ToString('o')}
    } else { [ordered]@{path=$path;missing=$true} }
}
$data = [ordered]@{schemaVersion=1; recordedUtc=[DateTime]::UtcNow.ToString('o');sourceRoot=$root;gameRoot=$GameRoot;
    localDataPresent=(Test-Path -LiteralPath (Join-Path $GameRoot 'LocalData') -PathType Container);
    files=@($files);runtimeTest='NOT PERFORMED';
    profile='Source/runtime data is local to this new project; no DataDir*.txt overrides permitted.'}
$data | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $docs 'BASELINE.json') -Encoding UTF8
Write-Host 'Baseline hashes recorded; this does not establish runtime compatibility.'
