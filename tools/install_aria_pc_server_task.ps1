param(
   [string]$TaskName = "Aria PC Local Website Server",
   [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
   [string]$HostAddress = "127.0.0.1",
   [int]$Port = 8787,
   [switch]$RunNow
)

$ErrorActionPreference = "Stop"

$python = (Get-Command py -ErrorAction Stop).Source
$serverScript = Join-Path $RepoRoot "tools\aria_pc_server.py"
if (-not (Test-Path -LiteralPath $serverScript)) {
   throw "Aria PC server script not found: $serverScript"
}

$arguments = "-B `"$serverScript`" --host $HostAddress --port $Port --nas-root `"$RepoRoot`" --allow-write"
$action = New-ScheduledTaskAction -Execute $python -Argument $arguments -WorkingDirectory $RepoRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
   -AllowStartIfOnBatteries `
   -DontStopIfGoingOnBatteries `
   -ExecutionTimeLimit (New-TimeSpan -Days 365) `
   -RestartCount 3 `
   -RestartInterval (New-TimeSpan -Minutes 1) `
   -StartWhenAvailable

Register-ScheduledTask `
   -TaskName $TaskName `
   -Action $action `
   -Trigger $trigger `
   -Settings $settings `
   -Description "Starts the read-only Aria PC local website server after user logon." `
   -Force `
   -ErrorAction Stop | Out-Null

if ($RunNow) {
   Start-ScheduledTask -TaskName $TaskName -ErrorAction Stop
}

[PSCustomObject]@{
   task_name    = $TaskName
   repo_root    = $RepoRoot
   url          = "http://${HostAddress}:$Port/"
   health_check = ".\tools\aria_pc_server_health.ps1 -BaseUrl http://${HostAddress}:$Port"
   run_now      = [bool]$RunNow
} | ConvertTo-Json -Depth 4

