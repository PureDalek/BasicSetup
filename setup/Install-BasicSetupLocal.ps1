# Install-BasicSetupLocal.ps1
# Download-first Windows bootstrapper for BasicSetup.
# This script does not require Git to download the repository.
# It can use winget to install base dependencies before launching BasicSetup locally.

param(
    [string]$RepositoryOwner = "PureDalek",
    [string]$RepositoryName = "BasicSetup",
    [string]$Branch = "main",
    [string]$InstallDirectory = "$env:LOCALAPPDATA\BasicSetup",
    [switch]$SkipWingetBootstrap,
    [switch]$SkipDependencyInstall,
    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[BasicSetup] $Message"
}

function Write-WarningStep {
    param([string]$Message)
    Write-Warning "[BasicSetup] $Message"
}

function Test-CommandAvailable {
    param([string]$CommandName)
    return $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

function Update-ProcessPath {
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
}

function Install-WingetIfMissing {
    if (Test-CommandAvailable -CommandName "winget") {
        Write-Step "winget is already available."
        return
    }

    if ($SkipWingetBootstrap) {
        Write-WarningStep "winget was not found and -SkipWingetBootstrap was provided."
        return
    }

    Write-Step "winget was not found. Downloading Microsoft App Installer bundle."

    $wingetBundlePath = Join-Path $env:TEMP "Microsoft.DesktopAppInstaller.msixbundle"

    Invoke-WebRequest `
        -Uri "https://aka.ms/getwinget" `
        -OutFile $wingetBundlePath `
        -UseBasicParsing

    try {
        Add-AppxPackage -Path $wingetBundlePath
        Update-ProcessPath
    }
    catch {
        Write-WarningStep "Automatic winget bootstrap failed: $($_.Exception.Message)"
        Write-WarningStep "Install 'App Installer' from Microsoft Store, then rerun this script."
    }
}

function Install-WingetPackage {
    param(
        [string]$PackageId,
        [string]$PackageDisplayName
    )

    if (-not (Test-CommandAvailable -CommandName "winget")) {
        Write-WarningStep "Skipping $PackageDisplayName because winget is unavailable."
        return
    }

    Write-Step "Installing or updating $PackageDisplayName through winget."

    $wingetArguments = @(
        "install",
        "--id", $PackageId,
        "--exact",
        "--silent",
        "--accept-package-agreements",
        "--accept-source-agreements"
    )

    & winget @wingetArguments

    if ($LASTEXITCODE -ne 0) {
        Write-WarningStep "winget returned exit code $LASTEXITCODE for $PackageDisplayName. Continuing."
    }

    Update-ProcessPath
}

function Install-BaseDependencies {
    if ($SkipDependencyInstall) {
        Write-Step "Skipping dependency installation because -SkipDependencyInstall was provided."
        return
    }

    Install-WingetIfMissing

    Install-WingetPackage -PackageId "Python.Python.3.12" -PackageDisplayName "Python 3.12"
    Install-WingetPackage -PackageId "Git.Git" -PackageDisplayName "Git"
}

function Download-BasicSetupArchive {
    param([string]$DestinationDirectory)

    $archiveUrl = "https://github.com/$RepositoryOwner/$RepositoryName/archive/refs/heads/$Branch.zip"
    $archivePath = Join-Path $env:TEMP "$RepositoryName-$Branch.zip"

    Write-Step "Downloading $archiveUrl"

    Invoke-WebRequest `
        -Uri $archiveUrl `
        -OutFile $archivePath `
        -UseBasicParsing

    if (Test-Path $DestinationDirectory) {
        Write-Step "Removing existing install directory: $DestinationDirectory"
        Remove-Item -Path $DestinationDirectory -Recurse -Force
    }

    $extractDirectory = Join-Path $env:TEMP "$RepositoryName-$Branch-extract"

    if (Test-Path $extractDirectory) {
        Remove-Item -Path $extractDirectory -Recurse -Force
    }

    New-Item -ItemType Directory -Force -Path $extractDirectory | Out-Null
    New-Item -ItemType Directory -Force -Path $DestinationDirectory | Out-Null

    Write-Step "Extracting archive."
    Expand-Archive -Path $archivePath -DestinationPath $extractDirectory -Force

    $expandedRepositoryRoot = Get-ChildItem -Path $extractDirectory -Directory | Select-Object -First 1

    if (-not $expandedRepositoryRoot) {
        throw "Could not find extracted repository root in $extractDirectory"
    }

    Write-Step "Copying BasicSetup into $DestinationDirectory"
    Copy-Item -Path (Join-Path $expandedRepositoryRoot.FullName "*") -Destination $DestinationDirectory -Recurse -Force
}

function Start-LocalBasicSetup {
    if ($NoLaunch) {
        Write-Step "Skipping launch because -NoLaunch was provided."
        return
    }

    $launcherPath = Join-Path $InstallDirectory "setup\BasicSetupLauncher.ps1"
    $batchLauncherPath = Join-Path $InstallDirectory "setup\run_full_setup.bat"
    $setupDirectory = Join-Path $InstallDirectory "setup"

    if (Test-Path $launcherPath) {
        Write-Step "Launching BasicSetup with local launcher."
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $launcherPath -SkipUpdate
        return
    }

    if (Test-Path $batchLauncherPath) {
        Write-Step "Launching BasicSetup with batch launcher."
        Start-Process -FilePath $batchLauncherPath -WorkingDirectory $setupDirectory -Wait
        return
    }

    throw "Could not find BasicSetup launcher under $setupDirectory"
}

Install-BaseDependencies
Download-BasicSetupArchive -DestinationDirectory $InstallDirectory
Start-LocalBasicSetup
