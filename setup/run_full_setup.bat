@echo off
:: BatchGotAdmin
:-------------------------------------
REM  --> Check for permissions
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

REM --> If error flag set, we do not have admin.
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "cmd.exe", "/c %~s0 %*", "", "runas", 1 >> "%temp%\getadmin.vbs"

    "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
    pushd "%CD%"
    CD /D "%~dp0"
:--------------------------------------

:: Check if Python is already installed and matches the desired version
echo Checking for Python installation...
for /f "delims=" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found %PYTHON_VERSION%

:: Extract the version number and compare
for /f "tokens=2 delims= " %%a in ("%PYTHON_VERSION%") do set INSTALLED_VERSION=%%a
if "%INSTALLED_VERSION%"=="3.12.0" (
    echo Python 3.12 is already installed.
) else (
    echo Installing Python 3.12...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "choco install python --version=3.12 -y"

    :: Add Python to the PATH
    :: Note: Adjust the Python path according to the specific version installed and the default Chocolatey install path
    set PATH=%PATH%;C:\Python312;C:\Python312\Scripts;
)

:: Running program_setup.py
echo Running program_setup.py...
python program_setup.py

exit
