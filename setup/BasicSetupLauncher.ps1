# BasicSetupLauncher.ps1
# Windows launcher for BasicSetup with optional repository auto-update.

param(
    [string]$RepositoryUrl = "https://github.com/PureDalek/BasicSetup.git",
    [string]$Branch = "main",
    [string]$InstallDirectory = "$env:LOCALAPPDATA\BasicSetup",
    [switch]$SkipUpdate
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[BasicSetup] $Message"
}

function Test-GitAvailable {
    return $null -ne (Get-Command git -ErrorAction SilentlyContinue)
}

function Get-RepositoryRoot {
    param([string]$ScriptDirectory)

    $candidateRoot = Resolve-Path (Join-Path $ScriptDirectory "..")

    if (Test-Path (Join-Path $candidateRoot ".git")) {
        return $candidateRoot.Path
    }

    return $InstallDirectory
}

function Update-Repository {
    param([string]$RepositoryRoot)

    if ($SkipUpdate) {
        Write-Step "Skipping update because -SkipUpdate was provided."
        return
    }

    if (-not (Test-GitAvailable)) {
        Write-Step "Git was not found. Skipping auto-update."
        return
    }

    if (-not (Test-Path $RepositoryRoot)) {
        Write-Step "Cloning $RepositoryUrl into $RepositoryRoot"
        git clone --branch $Branch $RepositoryUrl $RepositoryRoot
        return
    }

    if (-not (Test-Path (Join-Path $RepositoryRoot ".git"))) {
        Write-Step "Install directory exists but is not a git repository. Skipping auto-update: $RepositoryRoot"
        return
    }

    Push-Location $RepositoryRoot
    try {
        Write-Step "Fetching latest changes from origin/$Branch"
        git fetch origin $Branch

        Write-Step "Fast-forwarding local checkout"
        git checkout $Branch
        git pull --ff-only origin $Branch
    }
    finally {
        Pop-Location
    }
}

function Start-BasicSetup {
    param([string]$RepositoryRoot)

    $setupDirectory = Join-Path $RepositoryRoot "setup"
    $batchLauncher = Join-Path $setupDirectory "run_full_setup.bat"
    $pythonLauncher = Join-Path $setupDirectory "program_setup.py"

    if (Test-Path $batchLauncher) {
        Write-Step "Starting setup through run_full_setup.bat"
        Start-Process -FilePath $batchLauncher -WorkingDirectory $setupDirectory -Wait
        return
    }

    if (Test-Path $pythonLauncher) {
        Write-Step "Starting setup through program_setup.py"
        Push-Location $setupDirectory
        try {
            python $pythonLauncher
        }
        finally {
            Pop-Location
        }
        return
    }

    throw "Could not find a supported BasicSetup launcher in $setupDirectory"
}

$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$repositoryRoot = Get-RepositoryRoot -ScriptDirectory $scriptDirectory

Update-Repository -RepositoryRoot $repositoryRoot
Start-BasicSetup -RepositoryRoot $repositoryRoot
