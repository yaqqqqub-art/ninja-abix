@echo off
setlocal
title ABIX NINJA - Build Setup EXE
cd /d "%~dp0"

echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
  echo Python is not installed. Install it from https://www.python.org/downloads/
  echo IMPORTANT: tick "Add python.exe to PATH" in the installer, then run this file again.
  pause & exit /b 1
)

echo [2/4] Installing pygame + PyInstaller...
python -m pip install --upgrade pip
python -m pip install pygame pyinstaller numpy opencv-python
if errorlevel 1 ( echo pip install failed & pause & exit /b 1 )

echo [3/4] Building AbixNinja.exe ...
python -m PyInstaller --noconfirm --clean --windowed --name AbixNinja ^
  --icon assets\icon.ico --add-data "assets;assets" --collect-all pygame --hidden-import numpy --hidden-import cv2 intro.py
if errorlevel 1 ( echo PyInstaller failed & pause & exit /b 1 )

echo [4/4] Building Setup installer...
set ISCC=
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe
if "%ISCC%"=="" (
  echo.
  echo Game EXE is ready: dist\AbixNinja\AbixNinja.exe  ^(you can already play it^)
  echo To also make the Setup EXE, install Inno Setup 6 from https://jrsoftware.org/isdl.php
  echo and run this file again.
  pause & exit /b 0
)
"%ISCC%" setup.iss
if errorlevel 1 ( echo Inno Setup failed & pause & exit /b 1 )

echo.
echo DONE!  Your installer: installer_output\AbixNinja_Setup.exe
pause
