[CmdletBinding()]
param(
    [string[]]$Domains = @("guts-gigaflops.de", "www.guts-gigaflops.de")
)

$ErrorActionPreference = "Continue"
Write-Host "ARIA PC remote access check" -ForegroundColor Cyan
Write-Host ""

$tailscale = Get-Command tailscale -ErrorAction SilentlyContinue
if ($tailscale) {
    Write-Host "Tailscale: installed" -ForegroundColor Green
    $tailscaleIp = tailscale ip -4 2>$null | Select-Object -First 1
    if ($tailscaleIp) {
        Write-Host "Tailscale IPv4: $tailscaleIp" -ForegroundColor Green
    }
    else {
        Write-Host "Tailscale IPv4: unavailable; authenticate this device first" -ForegroundColor Yellow
    }
}
else {
    Write-Host "Tailscale: not installed" -ForegroundColor Yellow
    Write-Host "Install Tailscale on Aria PC, then run: tailscale up"
}

Write-Host ""
foreach ($domain in $Domains) {
    try {
        $records = Resolve-DnsName -Name $domain -Type A -ErrorAction Stop |
        Where-Object { $_.Type -eq "A" } |
        Select-Object -ExpandProperty IPAddress
        if ($records) {
            Write-Host "${domain}: $($records -join ', ')" -ForegroundColor Green
        }
        else {
            Write-Host "${domain}: no A record" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "${domain}: DNS lookup failed" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Local server remains private at http://127.0.0.1:8787/ or the trusted LAN address."
Write-Host "Do not forward port 8787 on the Vodafone router for Tailscale access."
