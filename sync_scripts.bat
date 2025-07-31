@echo off
echo SerialKiller2 Synchronized Script Launcher
echo ==========================================
echo.

REM Configuration - EDIT THESE VALUES FOR YOUR SETUP
set HELMHOLTZ_PORT=COM3
set SATELLITE_PORT=COM4
set HELMHOLTZ_SCRIPT=scripts/helmholtz_script.txt
set SATELLITE_SCRIPT=scripts/satellite_script.txt

echo Helmholtz Port: %HELMHOLTZ_PORT%
echo Satellite Port: %SATELLITE_PORT%
echo Helmholtz Script: %HELMHOLTZ_SCRIPT%
echo Satellite Script: %SATELLITE_SCRIPT%
echo.

REM Check if script files exist
if not exist "%HELMHOLTZ_SCRIPT%" (
    echo ERROR: Helmholtz script not found: %HELMHOLTZ_SCRIPT%
    pause
    exit /b 1
)

if not exist "%SATELLITE_SCRIPT%" (
    echo ERROR: Satellite script not found: %SATELLITE_SCRIPT%
    pause
    exit /b 1
)

echo Launching instances in 3 seconds...
timeout /t 1 /nobreak >nul
echo 3...
timeout /t 1 /nobreak >nul
echo 2...
timeout /t 1 /nobreak >nul
echo 1...
timeout /t 1 /nobreak >nul

echo LAUNCHING NOW!

REM Launch both instances simultaneously
start "Helmholtz SK2" python SK.py -c "con %HELMHOLTZ_PORT%" "script -o %HELMHOLTZ_SCRIPT%" "script"
start "Satellite SK2" python SK.py -c "con %SATELLITE_PORT%" "script -o %SATELLITE_SCRIPT%" "script"

echo Both instances launched!
echo Scripts should now be running on both instances!
pause 