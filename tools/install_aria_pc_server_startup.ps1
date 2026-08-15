param()
Write-Host "Installing Aria PC Server auto-startup..." -ForegroundColor Cyan
$startupDir = [Environment]::GetFolderPath([Environment+SpecialFolder]::Startup)
$shortcutPath = Join-Path $startupDir "AriaPcServer.lnk"
$cmdPath = (Get-Item "T:\NasDisk119\Aria\AEGIS\Guts&Gigaflopps\AriaPcServer.cmd").FullName
Write-Host "Startup folder: $startupDir" -ForegroundColor Gray
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $cmdPath
$shortcut.WorkingDirectory = (Get-Item "T:\NasDisk119\Aria").FullName
$shortcut.Description = "Aria PC Server - Local Status Dashboard"
$shortcut.IconLocation = "$cmdPath,0"
$shortcut.Save()
Write-Host "OK: Startup shortcut installed at $shortcutPath" -ForegroundColor Green
Write-Host "Server will start automatically on next Windows login." -ForegroundColor Green
Write-Host "View logs: .\reports\aria_pc_server.log" -ForegroundColor Gray# Start-Process is maintained for compatibility.
