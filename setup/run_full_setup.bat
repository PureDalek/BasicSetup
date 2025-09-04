@echo off
:: Elevate to Admin if needed
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else (
    goto GotAdmin
)

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "cmd.exe", "/c %~s0 %*", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B

:GotAdmin
    if exist "%temp%\getadmin.vbs" del "%temp%\getadmin.vbs"
    pushd "%CD%"
    CD /D "%~dp0"

    setlocal EnableDelayedExpansion

    :: Check if Chocolatey is installed
    where choco >nul 2>nul
    if %errorlevel% NEQ 0 (
        echo Chocolatey not found. Installing Chocolatey...
        powershell -NoProfile -ExecutionPolicy Bypass -Command ^
            "Set-ExecutionPolicy Bypass -Scope Process -Force; ^
            [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; ^
            iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    ) else (
        echo Chocolatey is already installed.
    )

    :: Check if Python is already installed and matches the desired version
    echo Checking for Python installation...
    for /f "delims=" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo Found !PYTHON_VERSION!

    for /f "tokens=2 delims= " %%a in ("!PYTHON_VERSION!") do set INSTALLED_VERSION=%%a
    for /f "tokens=1,2 delims=." %%b in ("!INSTALLED_VERSION!") do (
        set MAJOR_VERSION=%%b
        set MINOR_VERSION=%%c
    )

    if "!MAJOR_VERSION!"=="3" if !MINOR_VERSION! GEQ 12 (
        echo Python 3.12 or newer is already installed.
    ) else (
        echo Installing Python 3.12...
        powershell -NoProfile -ExecutionPolicy Bypass -Command "choco install python --version=3.12 -y"
        set PATH=!PATH!;C:\Python312;C:\Python312\Scripts;
    )

    :: Run your setup script
    echo Running program_setup.py...
    python program_setup.py

    endlocal
    exit /B