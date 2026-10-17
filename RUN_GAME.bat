@echo off
title ABIX NINJA
cd /d "%~dp0"
python --version >nul 2>&1
if errorlevel 1 (
  echo Python is not installed. Install from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
  pause & exit /b 1
)
python -c "import pygame, numpy, cv2" >nul 2>&1
if errorlevel 1 (
  echo Installing pygame, numpy, opencv-python ^(first time only, internet needed^)...
  python -m pip install pygame numpy opencv-python
  if errorlevel 1 ( echo pip install failed & pause & exit /b 1 )
)
python intro.py
if errorlevel 1 pause
