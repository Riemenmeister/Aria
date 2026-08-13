param(
   [string]$BaseUrl = "http://127.0.0.1:8787",
   [int]$IntervalSeconds = 240,
   [int]$Iterations = 0
)

$ErrorActionPreference = "Stop"

if ($IntervalSeconds -ge 300) {
   throw "IntervalSeconds must stay below the observed FRITZ!NAS 5-minute idle logout window. Use 240 seconds or less."
}

$count = 0
while ($true) {
   $timestamp = Get-Date -Format o
   try {
      $nas = Invoke-RestMethod -Uri "$BaseUrl/api/nas" -TimeoutSec 10
      [PSCustomObject]@{
         timestamp = $timestamp
         base_url = $BaseUrl
         nas_status = $nas.status
         can_list = $nas.can_list
         can_list_error_type = $nas.can_list_error_type
         root = $nas.root
      } | ConvertTo-Json -Depth 4
   }
   catch {
      [PSCustomObject]@{
         timestamp = $timestamp
         base_url = $BaseUrl
         nas_status = "probe_failed"
         error = $_.Exception.Message
      } | ConvertTo-Json -Depth 4
   }

   $count += 1
   if ($Iterations -gt 0 -and $count -ge $Iterations) {
      break
   }
   Start-Sleep -Seconds $IntervalSeconds
}