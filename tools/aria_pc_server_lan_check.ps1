param(
    [string]$BaseUrl = "http://127.0.0.1:8787",
    [string]$LanHost = "0.0.0.0"
)

$ErrorActionPreference = "Stop"

$ip = $null
$ipCandidates = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -and $_.IPAddress -ne "127.0.0.1" } |
    Select-Object -ExpandProperty IPAddress)

foreach ($candidate in $ipCandidates) {
    if ($candidate -match '^\d+\.\d+\.\d+\.\d+$' -and $candidate -notmatch '^169\.254\.' -and (
            $candidate -match '^10\.' -or
            $candidate -match '^192\.168\.' -or
            $candidate -match '^172\.(1[6-9]|2[0-9]|3[0-1])\.'
        )) {
        $ip = $candidate
        break
    }
}

if ([string]::IsNullOrWhiteSpace($ip)) {
    $lines = @(ipconfig | Select-String -Pattern "IPv4-Adresse|IPv4 Address")
    foreach ($line in $lines) {
        $match = [regex]::Match($line.ToString(), '(?:IPv4-Adresse|IPv4 Address)\s*[: ]+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)')
        if ($match.Success) {
            $candidate = $match.Groups[1].Value
            if ($candidate -notmatch '^169\.254\.' -and (
                    $candidate -match '^10\.' -or
                    $candidate -match '^192\.168\.' -or
                    $candidate -match '^172\.(1[6-9]|2[0-9]|3[0-1])\.'
                )) {
                $ip = $candidate
                break
            }
        }
    }
}

if ([string]::IsNullOrWhiteSpace($ip)) {
    foreach ($candidate in $ipCandidates) {
        if ($candidate -match '^\d+\.\d+\.\d+\.\d+$' -and $candidate -notmatch '^169\.254\.' -and $candidate -ne '127.0.0.1') {
            $ip = $candidate
            break
        }
    }
}

if ([string]::IsNullOrWhiteSpace($ip)) {
    throw "Could not determine the Aria PC LAN IPv4 address."
}

$lanUrl = "http://{0}:8787/api/health" -f $ip

[PSCustomObject]@{
    local_ip  = $ip
    local_url = $BaseUrl + "/api/health"
    lan_url   = $lanUrl
    lan_host  = $LanHost
    status    = "ready_for_lan_probe"
} | ConvertTo-Json -Depth 4

try {
    $health = Invoke-RestMethod -Uri $lanUrl -TimeoutSec 5
    [PSCustomObject]@{
        local_ip       = $ip
        lan_url        = $lanUrl
        service_status = $health.status
        ready_count    = $health.ready_count
        open_count     = $health.open_count
        nas_status     = $health.nas.status
        verified       = $true
    } | ConvertTo-Json -Depth 4
    exit 0
}
catch {
    [PSCustomObject]@{
        local_ip = $ip
        lan_url  = $lanUrl
        error    = $_.Exception.Message
        verified = $false
    } | ConvertTo-Json -Depth 4
    exit 2
}
