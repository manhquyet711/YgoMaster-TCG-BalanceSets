param([string]$RuntimeDirectory = $PSScriptRoot, [switch]$ValidateOnly)
$ErrorActionPreference = 'Stop'
# The mod accepts JSON comments and trailing commas. Windows PowerShell 5.1's
# ConvertFrom-Json does not, so normalize outside quoted strings first.
if (-not ('BalancedLaunchJson' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Text;
public static class BalancedLaunchJson {
    public static string Normalize(string source) {
        var clean = new StringBuilder();
        bool quoted = false, escaped = false;
        for (int i = 0; i < source.Length; i++) {
            char c = source[i];
            if (quoted) {
                clean.Append(c);
                if (escaped) escaped = false;
                else if (c == '\\') escaped = true;
                else if (c == '"') quoted = false;
                continue;
            }
            if (c == '"') { quoted = true; clean.Append(c); continue; }
            if (c == '/' && i + 1 < source.Length && source[i + 1] == '/') {
                clean.Append(' ');
                i += 2;
                while (i < source.Length && source[i] != '\r' && source[i] != '\n') i++;
                if (i < source.Length) clean.Append(source[i]);
                continue;
            }
            if (c == '/' && i + 1 < source.Length && source[i + 1] == '*') {
                clean.Append(' ');
                i += 2;
                while (i + 1 < source.Length && !(source[i] == '*' && source[i + 1] == '/')) {
                    if (source[i] == '\r' || source[i] == '\n') clean.Append(source[i]);
                    i++;
                }
                if (i + 1 >= source.Length) throw new FormatException("Unterminated JSON block comment.");
                i++;
                continue;
            }
            clean.Append(c);
        }
        if (quoted) throw new FormatException("Unterminated JSON string.");
        string text = clean.ToString();
        var result = new StringBuilder();
        quoted = false; escaped = false;
        for (int i = 0; i < text.Length; i++) {
            char c = text[i];
            if (quoted) {
                result.Append(c);
                if (escaped) escaped = false;
                else if (c == '\\') escaped = true;
                else if (c == '"') quoted = false;
                continue;
            }
            if (c == '"') quoted = true;
            if (c == ',') {
                int next = i + 1;
                while (next < text.Length && Char.IsWhiteSpace(text[next])) next++;
                if (next < text.Length && (text[next] == '}' || text[next] == ']')) continue;
            }
            result.Append(c);
        }
        return result.ToString();
    }
}
'@
}
function Read-BalancedConfig([string]$Path) {
    try {
        $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
        return ([BalancedLaunchJson]::Normalize($raw) | ConvertFrom-Json)
    } catch { throw "Cannot read config '$Path': $($_.Exception.Message)" }
}
$root = [IO.Path]::GetFullPath($RuntimeDirectory)
$logs = Join-Path $root 'LaunchLogs'
try {
    $settings = Read-BalancedConfig (Join-Path $root 'Data\Settings.json')
    $client = Read-BalancedConfig (Join-Path $root 'Data\ClientData\ClientSettings.json')
    $port = [int]$settings.BasePort
    $sessionPort = [int]$settings.SessionServerPort
    if ($port -lt 1 -or $port -gt 65535 -or $sessionPort -lt 1 -or $sessionPort -gt 65535 -or $port -eq $sessionPort) { throw 'Invalid server ports.' }
    if ([int]$client.BasePort -ne $port -or [int]$client.SessionServerPort -ne $sessionPort) { throw 'Client and server ports differ. Match them before starting.' }
    foreach ($file in @('YgoMaster.exe','YgoMasterClient.exe','YgoMasterLoader.dll','Data\BalancedCharacters\Mode.json')) {
        if (-not (Test-Path -LiteralPath (Join-Path $root $file) -PathType Leaf)) { throw "Missing balanced runtime file: $file" }
    }
    $gameRoot = Split-Path -Parent $root
    if (-not (Test-Path -LiteralPath (Join-Path $gameRoot 'masterduel.exe') -PathType Leaf)) { throw 'Install this runtime beside masterduel.exe.' }
    if (-not (Test-Path -LiteralPath (Join-Path $gameRoot 'LocalData') -PathType Container)) { throw 'Downloaded LocalData is missing.' }
    if ($ValidateOnly) { Write-Output "PASS balanced launch paths and matching configured ports: $port / $sessionPort"; return }
    if (Get-Process -Name masterduel -ErrorAction SilentlyContinue) { throw 'Close Master Duel before starting another session.' }
    $serverPath = Join-Path $root 'YgoMaster.exe'
    # A stopped game permits restarting only this runtime's own server so
    # newly saved settings are loaded. Other mod servers are left alone.
    $own = @(Get-Process -Name YgoMaster -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $serverPath })
    foreach ($process in $own) { Stop-Process -Id $process.Id; if (-not $process.WaitForExit(5000)) { throw 'Balanced server did not stop.' } }
    $listeners = [Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners()
    if ($listeners | Where-Object { $_.Port -eq $port -or $_.Port -eq $sessionPort }) { throw "Configured port $port or $sessionPort is occupied by another process." }
    New-Item -ItemType Directory -Path $logs -Force | Out-Null
    $stamp = [DateTime]::Now.ToString('yyyyMMdd-HHmmss-fff')
    $started = Start-Process -FilePath $serverPath -WorkingDirectory $root -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $logs "$stamp-server.log") -RedirectStandardError (Join-Path $logs "$stamp-server-error.log")
    $ready = $false
    for ($i = 0; $i -lt 150; $i++) {
        $started.Refresh()
        if ($started.HasExited) { throw "Balanced server exited. See $logs" }
        $activePorts = @([Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners() | Select-Object -ExpandProperty Port)
        if ($activePorts -contains $port -and $activePorts -contains $sessionPort) { $ready = $true; break }
        Start-Sleep -Milliseconds 100
    }
    if (-not $ready) { throw "Server did not open configured ports $port / $sessionPort. See $logs" }
    Start-Process -FilePath (Join-Path $root 'YgoMasterClient.exe') -WorkingDirectory $root -WindowStyle Hidden
    Write-Output "Started balanced server/client on configured ports $port / $sessionPort."
} catch {
    if (-not $ValidateOnly) {
        try { New-Item -ItemType Directory -Path $logs -Force | Out-Null; $_.Exception.Message | Add-Content -LiteralPath (Join-Path $logs 'Launcher-errors.log') } catch { }
    }
    throw
}
