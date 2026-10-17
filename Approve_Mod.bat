@echo off
cd /d "%~dp0"
if "%~1"=="" (
  echo Drag a MOD FOLDER onto this file to approve it.
  pause & exit /b 1
)
python security_server\abix_security_server.py approve "%~1"
pause
