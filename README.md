# BasicSetup

BasicSetup is a small Windows and Linux bootstrapper for setting up a fresh machine from reusable software profiles.

It provides:

- A tracked application version in `VERSION`, shown in the GUI with the current Git commit.
- A Tkinter setup UI for choosing predefined install profiles or a custom package list.
- A basic JSON software catalog plus an optional catalog that can be loaded on request.
- JSON-backed setup profiles that can be saved from the GUI.
- A local download bootstrapper for fresh Windows installs.
- A Windows launcher with optional auto-update support.
- Chocolatey-based Windows installs.
- Linux installs through snap, apt, dnf, or yum where supported.

## Repository layout

```text
BasicSetup/
|-- VERSION                         # Current application version shown in the GUI
|-- ROADMAP.md                      # Improvement ideas and future workflow notes
|-- setup/
|   |-- BasicSetupLauncher.ps1       # Windows launcher with optional Git auto-update
|   |-- Install-BasicSetupLocal.ps1  # Download-first Windows installer with winget dependency setup
|   |-- Elevate.ps1                  # Elevated Chocolatey wrapper
|   |-- blueprint.config             # Setup profiles
|   |-- catalog_extra.json           # Optional software catalog loaded on request
|   |-- program_setup.py             # Tkinter UI
|   |-- run_full_setup.bat           # Windows bootstrap entrypoint
|   |-- software.json                # Software package catalog
|   `-- software_installer.py        # Package install logic
|-- tests/
|   `-- test_basicsetup_config.py    # Config and installer tests
`-- requirements.txt
```

## Requirements

### Windows

- Windows 10 or newer
- PowerShell
- winget, optional but recommended for the local bootstrapper
- Git, optional for launcher auto-update support
- Chocolatey, installed automatically by `run_full_setup.bat` when missing
- Python 3.12 or newer, installed automatically by `run_full_setup.bat` when missing

### Linux

- Python 3.12 or newer
- One supported package manager:
  - `snap`
  - `apt-get`
  - `dnf`
  - `yum`

## Best fresh Windows install

This option does not require Git to download BasicSetup. It downloads the repository ZIP locally, installs base dependencies through winget when available, then launches the setup flow.

From PowerShell:

```powershell
$installerPath = "$env:TEMP\Install-BasicSetupLocal.ps1"
Invoke-WebRequest `
    -Uri "https://raw.githubusercontent.com/PureDalek/BasicSetup/main/setup/Install-BasicSetupLocal.ps1" `
    -OutFile $installerPath

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installerPath
```

By default, this installs the repo into:

```powershell
$env:LOCALAPPDATA\BasicSetup
```

### Local installer options

Install from a different branch:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installerPath -Branch "main"
```

Use a custom install directory:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installerPath -InstallDirectory "C:\Tools\BasicSetup"
```

Skip winget bootstrap:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installerPath -SkipWingetBootstrap
```

Skip dependency installation:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installerPath -SkipDependencyInstall
```

Download only, without launching setup:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installerPath -NoLaunch
```

## GUI usage

Launch the GUI through the Windows batch file:

```powershell
.\setup\run_full_setup.bat
```

Or run it directly when Python is already installed:

```powershell
python .\setup\program_setup.py
```

Use dry-run mode to verify a profile without installing packages:

```powershell
python .\setup\program_setup.py --dry-run
```

The UI keeps profile installs and custom installs in the same status table. Package installs run in the background so the window remains responsive, and each package gets a final status.

The default install surface is intentionally small. Basic profiles include:

- `Developer`
- `Games`
- `AI`

Use the `Catalog` tab and `Load More Catalog` button to pull in optional apps such as RustDesk, Claude, LM Studio, Slack, remote tools, and additional developer utilities. Selected catalog apps can be added to the custom install list.

Custom selections can be saved as profiles. Profiles are stored in `setup/blueprint.config`, so changes are visible in Git and can be reviewed in a PR.

The `Catalog` tab can also scan the loaded catalog for apps already installed on the PC and save those installed apps as a new profile.

The GUI also checks for:

- BasicSetup updates from the configured Git upstream.
- Already installed packages through the local package manager.

Installed packages are marked in the status table and skipped during install runs.

The window title and header show the tracked app version from `VERSION` plus the current Git commit when available.

The update channel selector controls which Git branch is checked:

- `Stable` checks `main`.
- `Nightly` checks the Codex PR branch for in-progress builds.

After an update is applied, the GUI offers to restart and relaunch itself.

## Git auto-update launcher

Use this when BasicSetup already exists locally as a Git checkout.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\setup\BasicSetupLauncher.ps1
```

The launcher will:

1. Detect the repository location.
2. Pull the latest changes with Git when possible.
3. Start `setup/run_full_setup.bat`.
4. Launch the setup UI.

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

- `Developer`
- `Games`
- `AI`

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

Basic software metadata lives in `setup/software.json`. Optional software metadata lives in `setup/catalog_extra.json` and is loaded only when requested from the GUI.

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
- Core first-run profiles
- GUI config loading from the script directory
- Package key whitespace issues
- Windows installer command routing
- Linux snap routing

## Creating a release

This repository includes a tag-based release workflow.

Before tagging a release, update `VERSION` to the release number.

After merging changes into `main`, create and push a version tag:

```powershell
git checkout main
git pull origin main
git tag v0.1.0
git push origin v0.1.0
```

GitHub Actions will create a release and upload a ZIP package containing the setup files.

## Notes

- `program_setup.py` can be launched from any working directory because it loads config files relative to its own script path.
- Package installation changes the local machine. Review `software.json` before running a full profile.
- Linux support is best-effort and depends on package availability in the configured package manager.
