param([string]$AriaHost="127.0.0.1",[int]$Port=8787)
Write-Host "Aria PC System Validation" -ForegroundColor Cyan
$checks = @()
try {
  $h = Invoke-RestMethod -Uri "http://${AriaHost}:${Port}/api/health" -TimeoutSec 5
  if ($h.service -eq "aria-pc-server") {
    Write-Host "OK: Server running, NAS=$($h.nas.status), Ready=$($h.ready_count)/10" -ForegroundColor Green
    $checks += "Server:OK"
  }
}
catch { Write-Host "FAIL: Server unreachable" -ForegroundColor Red; $checks += "Server:FAIL" }

try {
  $n = Invoke-RestMethod -Uri "http://${AriaHost}:${Port}/api/nas" -TimeoutSec 5
  Write-Host "OK: NAS accessible, Resilience=$($n.session_resilience.risk)" -ForegroundColor Green
  $checks += "NAS:OK"
}
catch { Write-Host "FAIL: NAS check failed" -ForegroundColor Red; $checks += "NAS:FAIL" }

try {
  $d = Invoke-RestMethod -Uri "http://${AriaHost}:${Port}/api/device-mesh" -TimeoutSec 5
  Write-Host "OK: Device mesh=$($d.device_count) devices" -ForegroundColor Green
  $checks += "Mesh:OK"
}
catch { Write-Host "FAIL: Device mesh unreachable" -ForegroundColor Red; $checks += "Mesh:FAIL" }

$ts = Get-Command tailscale -EA SilentlyContinue
if ($ts) {
  $tip = (& tailscale ip -4 2>$null) | Select -First 1
  if ($tip) { Write-Host "OK: Tailscale authenticated at $tip" -ForegroundColor Green; $checks += "Tailscale:OK" }
  else { Write-Host "WARN: Tailscale not authenticated" -ForegroundColor Yellow; $checks += "Tailscale:WARN" }
}
else { Write-Host "WARN: Tailscale not installed" -ForegroundColor Yellow; $checks += "Tailscale:WARN" }

Write-Host ""
$summary = $checks -join " | "
Write-Host "Summary: $summary" -ForegroundColor Cyan
if ($summary -match "FAIL") { exit 1 } else { exit 0 }

