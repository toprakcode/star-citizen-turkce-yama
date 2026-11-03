@echo off
chcp 65001 >nul
setlocal
set "SRC=%~dp0global.ini"
if not exist "%SRC%" goto nosrc
set "GAME=%~1"
if "%GAME%"=="" set /p GAME=Star Citizen LIVE klasoru nerede? (ornek: S:\StarCitizen\LIVE): 
set "GAME=%GAME:"=%"
if not exist "%GAME%\Data.p4k" goto nogame
set "DIR=%GAME%\data\Localization\english"
if not exist "%DIR%" mkdir "%DIR%"
if exist "%DIR%\global.ini" if not exist "%DIR%\global.ini.en.bak" copy "%DIR%\global.ini" "%DIR%\global.ini.en.bak" >nul
copy /y "%SRC%" "%DIR%\global.ini" >nul
if errorlevel 1 goto copyfail
findstr /i /c:"g_language" "%GAME%\user.cfg" >nul 2>&1
if errorlevel 1 echo g_language = english>> "%GAME%\user.cfg"
echo.
echo Tamam! Turkce yama kuruldu. Oyunu tamamen kapatip yeniden ac.
echo Oyundaki dil ayari English kalsin.
pause
exit /b 0
:nosrc
echo global.ini bu dosyanin yaninda bulunamadi. Releases sayfasindan indirdigin global.ini'yi kur.bat ile ayni klasore koy.
pause
exit /b 1
:nogame
echo "%GAME%" icinde Data.p4k bulunamadi. Dogru LIVE klasorunu yazdigindan emin ol.
pause
exit /b 1
:copyfail
echo Kopyalama basarisiz. kur.bat dosyasina sag tiklayip "Yonetici olarak calistir" dene.
pause
exit /b 1
