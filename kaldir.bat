@echo off
chcp 65001 >nul
setlocal
set "GAME=%~1"
if "%GAME%"=="" set /p GAME=Star Citizen LIVE klasoru nerede? (ornek: S:\StarCitizen\LIVE): 
set "GAME=%GAME:"=%"
set "DIR=%GAME%\data\Localization\english"
if not exist "%DIR%\global.ini.en.bak" goto nobak
copy /y "%DIR%\global.ini.en.bak" "%DIR%\global.ini" >nul
echo Orijinal Ingilizce dosya geri yuklendi.
pause
exit /b 0
:nobak
echo Yedek (global.ini.en.bak) bulunamadi. Launcher'dan Verify Files ile orijinali geri yukleyebilirsin.
pause
exit /b 1
