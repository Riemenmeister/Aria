param(
   [string]$BaseUrl = "http://127.0.0.1:8787",
   [string]$RecordPath = ""
)

$ErrorActionPreference = "Stop"

function Test-AriaEndpoint {
   param(
      [string]$BaseUrl,
      [string]$Path
   )

   $uri = "$BaseUrl$Path"
   try {
      $response = Invoke-RestMethod -Uri $uri -TimeoutSec 5
      return [PSCustomObject]@{
         path = $Path
         uri = $uri
         status = "ok"
         response_status = $response.status
      }
   }
   catch {
      return [PSCustomObject]@{
         path = $Path
         uri = $uri
         status = "failed"
         error = $_.Exception.Message
      }
   }
}

$health = Invoke-RestMethod -Uri "$BaseUrl/api/health" -TimeoutSec 5
$mesh = Invoke-RestMethod -Uri "$BaseUrl/api/device-mesh" -TimeoutSec 5

$deviceChecks = @()
foreach ($device in $mesh.devices) {
   foreach ($path in $device.required_checks) {
      $deviceChecks += [PSCustomObject]@{
         device_id = $device.id
         device_status = $device.status
         check = (Test-AriaEndpoint -BaseUrl $BaseUrl -Path $path)
      }
   }
}

$failedChecks = @($deviceChecks | Where-Object { $_.check.status -ne "ok" })
$remotePending = @($mesh.devices | Where-Object { $_.role -ne "host" -and $_.status -like "*pending*" })

$result = [PSCustomObject]@{
   project = "Aria Device Mesh"
   status = if ($health.status -eq "ok" -and $mesh.device_count -ge 1 -and $failedChecks.Count -eq 0) { "local_mesh_endpoints_verified" } else { "degraded" }
   base_url = $BaseUrl
   server_status = $health.status
   device_count = $mesh.device_count
   verified_count = $mesh.verified_count
   pending_count = $mesh.pending_count
   remote_clients_pending_live_check = @($remotePending | ForEach-Object { $_.id })
   endpoint_checks = $deviceChecks
   guardrails = $mesh.guardrails
   next_verification = $mesh.next_verification
}

$json = $result | ConvertTo-Json -Depth 8
$json

if ($RecordPath -ne "") {
   $json | Set-Content -Path $RecordPath -Encoding UTF8
}

if ($result.status -ne "local_mesh_endpoints_verified") {
   exit 2
}