param()

Write-Host "Aria PC Tailscale Setup Automation" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if Tailscale is installed
$tailscale = Get-Command tailscale -ErrorAction SilentlyContinue
if (-not $tailscale) {
    Write-Host "Installing Tailscale..." -ForegroundColor Yellow
    
    # Verify winget is available
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        Write-Host "ERROR: winget is not available. Install Tailscale manually from https://tailscale.com/download/windows" -ForegroundColor Red
        exit 1
    }
    
    # Install Tailscale
    Write-Host "Running: winget install --id Tailscale.Tailscale --exact" -ForegroundColor Gray
    & winget install --id Tailscale.Tailscale --exact 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Installation failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
        exit 1
    }
    Write-Host "OK: Tailscale installed successfully" -ForegroundColor Green
    Start-Sleep -Seconds 2
}
else {
    Write-Host "OK: Tailscale is already installed" -ForegroundColor Green
}

Write-Host ""

# Step 2: Check if authenticated
$authCheck = & tailscale status 2>&1 | Select-Object -First 1
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK: Tailscale is already authenticated" -ForegroundColor Green
    $ipv4 = (& tailscale ip -4 2>$null) | Select-Object -First 1
    if ($ipv4) {
        Write-Host "   Tailscale IPv4: $ipv4" -ForegroundColor Green
    }
}
else {
    Write-Host "Launching Tailscale authentication..." -ForegroundColor Yellow
    Write-Host "Follow the browser prompt to authenticate." -ForegroundColor Gray
    Write-Host ""
    
    & tailscale up 2>&1 | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Authentication failed" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "OK: Authentication complete" -ForegroundColor Green
    
    Start-Sleep -Seconds 1
    $ipv4 = (& tailscale ip -4 2>$null) | Select-Object -First 1
    if ($ipv4) {
        Write-Host "   Tailscale IPv4: $ipv4" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Access Aria PC from your Tailscale network:" -ForegroundColor Cyan
Write-Host "  http://<TAILSCALE_IP>:8787/" -ForegroundColor Yellow
Write-Host ""
Write-Host "Port 8787 is private to Tailscale and will NOT appear on the router." -ForegroundColor Gray
Write-Host ""
Write-Host "Verify setup with:" -ForegroundColor Gray
Write-Host "  .\tools\aria_remote_access_check.ps1"
