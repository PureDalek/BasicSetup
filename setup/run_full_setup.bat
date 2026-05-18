@echo off
setlocal EnableExtensions

>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if not "%errorlevel%"=="0" (
    echo Requesting administrative privileges...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /B
)

cd /D "%~dp0"

where choco >nul 2>nul
if not "%errorlevel%"=="0" (
    echo Chocolatey not found. Installing Chocolatey...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    if exist "%ALLUSERSPROFILE%\chocolatey\bin" set "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
    call refreshenv >nul 2>nul
) else (
    echo Chocolatey is already installed.
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "if (Get-Command python -ErrorAction SilentlyContinue) { $version = [version]((python --version 2>&1) -replace 'Python ', ''); if ($version -ge [version]'3.12') { exit 0 } }; exit 1"
if not "%errorlevel%"=="0" (
    echo Installing Python 3.12...
    choco install python --version=3.12.0 -y
    if exist "C:\Python312" set "PATH=%PATH%;C:\Python312;C:\Python312\Scripts"
    call refreshenv >nul 2>nul
)

echo Running BasicSetup...
python "%~dp0program_setup.py"

endlocal
