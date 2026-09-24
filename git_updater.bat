@echo off
title Code Updater by Shawon
cls

echo ==========================================
echo           CODE UPDATER BY SHAWON          
echo ==========================================
echo.

:: Prompt the user for the commit name
set /p commit_name="Enter your commit name/message: "

echo.
echo Running Git commands...
echo.

:: Execute the Git commands
git add .
git commit -m "%commit_name%"
git push

echo.
echo ==========================================
echo  Update complete!
echo  Copyright by Shawon
echo ==========================================
echo.
pause