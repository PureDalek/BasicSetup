# BasicSetup

BasicSetup is a small Windows and Linux bootstrapper for setting up a fresh machine from reusable software profiles.

It provides:

- A Tkinter setup UI for choosing predefined install profiles.
- A JSON software catalog for Windows and Linux package names.
- A Windows launcher with optional auto-update support.
- Chocolatey-based Windows installs.
- Linux installs through snap, apt, dnf, or yum where supported.

## Repository layout

```text
BasicSetup/
├── setup/
│   ├── BasicSetupLauncher.ps1     # Windows launcher with optional auto-update
│   ├── Elevate.ps1                # Elevated Chocolatey wrapper
│   ├── blueprint.config           # Setup profiles
│   ├── program_setup.py           # Tkinter UI
│   ├── run_full_setup.bat         # Windows bootstrap entrypoint
│   ├── software.json              # Software package catalog
│   └── software_installer.py      # Package install logic
├── tests/
│   └── test_basicsetup_config.py  # Config and installer tests
└── requirements.txt
```

## Requirements

### Windows

- Windows 10 or newer
- PowerShell
- Git, for launcher auto-update support
- Chocolatey, installed automatically by `run_full_setup.bat` when missing
- Python 3.12 or newer, installed automatically by `run_full_setup.bat` when missing

### Linux

- Python 3.12 or newer
- One supported package manager:
  - `snap`
  - `apt-get`
  - `dnf`
  - `yum`

## Quick start on Windows

From PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\setup\BasicSetupLauncher.ps1
```

The launcher will:

1. Detect the repository location.
2. Pull the latest changes with Git when possible.
3. Start `setup/run_full_setup.bat`.
4. Launch the setup UI.

## Install from a fresh Windows machine

Download the launcher first, then run it:

```powershell
$launcherPath = "$env:TEMP\BasicSetupLauncher.ps1"
Invoke-WebRequest `
    -Uri "https://raw.githubusercontent.com/PureDalek/BasicSetup/main/setup/BasicSetupLauncher.ps1" `
    -OutFile $launcherPath

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $launcherPath
```

By default, the launcher clones or updates this repository into:

```powershell
$env:LOCALAPPDATA\BasicSetup
```

## Launcher options

```powershell
.\setup\BasicSetupLauncher.ps1 `
    -RepositoryUrl "https://github.com/PureDalek/BasicSetup.git" `
    -Branch "main" `
    -InstallDirectory "$env:LOCALAPPDATA\BasicSetup"
```

Skip auto-update:

```powershell
.\setup\BasicSetupLauncher.ps1 -SkipUpdate
```

Use a test branch:

```powershell
.\setup\BasicSetupLauncher.ps1 -Branch "improve-bootstrapper-tests"
```

## Setup profiles

Profiles are configured in `setup/blueprint.config`.

Current profiles:

- `Game`
- `Work`
- `Biznoe`
- `Bridgify`

Each profile is a list of software names that must exist in `setup/software.json`.

Example:

```json
{
    "Work": [
        "Visual Studio Code",
        "DBeaver",
        "Postman",
        "Google Chrome"
    ]
}
```

## Software catalog

Software metadata lives in `setup/software.json`.

Example entry:

```json
{
    "Visual Studio Code": {
        "windows_package": "vscode",
        "linux_package": "code",
        "linux_repo": null
    }
}
```

Supported optional fields:

```json
{
    "linux_repo": "ppa:example/project",
    "is_snap": true,
    "from_site": "https://example.com/download"
}
```

## Running tests

From the repository root:

```powershell
python -m pip install pytest
python -m pytest -v
```

The tests validate:

- JSON config syntax
- Profile/package consistency
- Package key whitespace issues
- Windows installer command routing
- Linux snap routing

## Creating a release

This repository includes a tag-based release workflow.

After merging changes into `main`, create and push a version tag:

```powershell
git checkout main
git pull origin main
git tag v0.1.0
git push origin v0.1.0
```

GitHub Actions will create a release and upload a ZIP package containing the setup files.

## Notes

- `program_setup.py` should normally be launched from inside the `setup` directory or through the provided wrapper/batch launcher.
- Package installation changes the local machine. Review `software.json` before running a full profile.
- Linux support is best-effort and depends on package availability in the configured package manager.
