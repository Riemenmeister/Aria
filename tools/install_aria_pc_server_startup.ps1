param(
   [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
   [string]$HostAddress = "127.0.0.1",
   [int]$Port = 8787,
   [string]$StartupFileName = "AriaPcServer.cmd",
   [switch]$StartNow
)

$ErrorActionPreference = "Stop"

$startupDirectory = [Environment]::GetFolderPath("Startup")
if (-not $startupDirectory) {
   throw "Could not resolve the current user's Startup folder."
}

$python = (Get-Command py -ErrorAction Stop).Source
$serverScript = Join-Path $RepoRoot "tools\aria_pc_server.py"
if (-not (Test-Path -LiteralPath $serverScript)) {
   throw "Aria PC server script not found: $serverScript"
}

$startupFile = Join-Path $startupDirectory $StartupFileName
$cmd = @"
@echo off
cd /d "$RepoRoot"
"$python" -B "$serverScript" --host $HostAddress --port $Port --nas-root "$RepoRoot" --allow-write
"@
Set-Content -Path $startupFile -Value $cmd -Encoding ASCII

if ($StartNow) {
   Start-Process -FilePath $python -ArgumentList @('-B', $serverScript, '--host', $HostAddress, '--port', [string]$Port, '--nas-root', $RepoRoot) -WorkingDirectory $RepoRoot -WindowStyle Hidden | Out-Null
}

[PSCustomObject]@{
   startup_file = $startupFile
   repo_root = $RepoRoot
   url = "http://${HostAddress}:$Port/"
   health_check = ".\tools\aria_pc_server_health.ps1 -BaseUrl http://${HostAddress}:$Port"
   start_now = [bool]$StartNow
} | ConvertTo-Json -Depth 4
