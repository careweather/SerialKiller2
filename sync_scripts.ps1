# SerialKiller2 Synchronized Script Launcher (PowerShell)
# This script provides the highest precision synchronization

param(
    [string]$HelmholtzPort = "COM3",
    [string]$SatellitePort = "COM4", 
    [string]$HelmholtzScript = "scripts/helmholtz_script.txt",
    [string]$SatelliteScript = "scripts/satellite_script.txt",
    [switch]$Help
)

if ($Help) {
    Write-Host "SerialKiller2 Synchronized Script Launcher"
    Write-Host "Usage: .\sync_scripts.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -HelmholtzPort <port>     Helmholtz COM port (default: COM3)"
    Write-Host "  -SatellitePort <port>     Satellite COM port (default: COM4)"
    Write-Host "  -HelmholtzScript <path>   Helmholtz script file (default: scripts/helmholtz_script.txt)"
    Write-Host "  -SatelliteScript <path>   Satellite script file (default: scripts/satellite_script.txt)"
    Write-Host "  -Help                     Show this help message"
    exit 0
}

Write-Host "SerialKiller2 Synchronized Script Launcher" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "Helmholtz Port: $HelmholtzPort"
Write-Host "Satellite Port: $SatellitePort" 
Write-Host "Helmholtz Script: $HelmholtzScript"
Write-Host "Satellite Script: $SatelliteScript"
Write-Host ""

# Verify script files exist
if (-not (Test-Path $HelmholtzScript)) {
    Write-Host "ERROR: Helmholtz script not found: $HelmholtzScript" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path $SatelliteScript)) {
    Write-Host "ERROR: Satellite script not found: $SatelliteScript" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Launching instances in 3 seconds..." -ForegroundColor Green
for ($i = 3; $i -gt 0; $i--) {
    Write-Host "$i..." -ForegroundColor Yellow
    Start-Sleep -Seconds 1
}

Write-Host "LAUNCHING NOW!" -ForegroundColor Red

# Create job scriptblocks for maximum synchronization
$helmholtzJob = {
    param($port, $script)
    Start-Process -FilePath "python" -ArgumentList @("SK.py", "-c", "con $port", "script -o $script", "script") -WindowStyle Normal
}

$satelliteJob = {
    param($port, $script) 
    Start-Process -FilePath "python" -ArgumentList @("SK.py", "-c", "con $port", "script -o $script", "script") -WindowStyle Normal
}

# Record start time
$startTime = Get-Date

# Start both jobs simultaneously
$job1 = Start-Job -ScriptBlock $helmholtzJob -ArgumentList $HelmholtzPort, $HelmholtzScript
$job2 = Start-Job -ScriptBlock $satelliteJob -ArgumentList $SatellitePort, $SatelliteScript

# Wait for both jobs to complete
Wait-Job $job1, $job2 | Out-Null

# Calculate execution time
$endTime = Get-Date
$executionTime = ($endTime - $startTime).TotalMilliseconds

# Clean up jobs
Remove-Job $job1, $job2

Write-Host ""
Write-Host "Both instances launched in $([math]::Round($executionTime, 2))ms" -ForegroundColor Green
Write-Host "Scripts should now be running on both instances!" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to exit" 