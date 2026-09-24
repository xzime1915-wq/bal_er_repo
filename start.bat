@echo off
title SENZ Desktop
cd /d "%~dp0"

if not exist .env (
  if exist .env.example copy .env.example .env
  echo Add GEMINI_API_KEY in .env then run again.
  notepad .env
  exit /b 1
)

echo.
echo  SENZ Desktop starting...
echo.

if not exist "frontend\node_modules\" (
  echo Installing...
  call npm install --prefix frontend
)

cd /d "%~dp0frontend"
call npm run desktop
