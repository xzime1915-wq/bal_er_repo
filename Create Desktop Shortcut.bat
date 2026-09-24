@echo off
set SCRIPT=%~dp0start.bat
set SHORTCUT=%USERPROFILE%\Desktop\SENZ.lnk

powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%SCRIPT%'; $s.WorkingDirectory = '%~dp0'; $s.WindowStyle = 1; $s.Description = 'SENZ AI Desktop'; $s.Save()"

echo Desktop shortcut created: %SHORTCUT%
pause
