param(
   [string]$BaseUrl = "http://127.0.0.1:8787"
)

$ErrorActionPreference = "Stop"

$health = Invoke-RestMethod -Uri "$BaseUrl/api/health" -TimeoutSec 5
$nas = Invoke-RestMethod -Uri "$BaseUrl/api/nas" -TimeoutSec 5

$result = [PSCustomObject]@{
   base_url = $BaseUrl
   service_status = $health.status
   nas_status = $nas.status
   nas_root = $nas.root
   nas_can_list = $nas.can_list
   ready_count = $health.ready_count
   open_count = $health.open_count
}

$result | ConvertTo-Json -Depth 4

if ($health.status -ne "ok" -or $nas.status -ne "ok") {
   exit 2
}
