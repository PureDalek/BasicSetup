# Changelog

All notable changes to BasicSetup will be documented in this file.

## Unreleased

### Added

- Added tracked app version display in the GUI and a root `VERSION` file.
- Added GUI update channel selection with `Stable` mapped to `main` and `Nightly` mapped to the Codex PR branch.
- Added a built-in `AI` profile for ChatGPT, Codex, Ollama, and supporting developer tools.
- Added an optional catalog view with on-demand catalog loading and RustDesk support.
- Added GUI profile saving/deleting backed by `setup/blueprint.config`.
- Added `ROADMAP.md` with concrete next-step ideas for catalog editing, Git-backed saves, versioning, and safer installs.
- Rebuilt the Tkinter GUI with profile selection, custom package selection, background installs, per-package status, and dry-run mode.
- Added GUI update checks with a manual fast-forward update action.
- Added installed-package detection and automatic skipping for packages already present on the machine.
- Added `Games`, `Custom Play`, and `Developer Workstation` setup profiles.
- Added Discord to the software catalog.
- Added tests for core profile availability and GUI config loading.

### Changed

- Hardened the Windows batch bootstrapper's Python detection and install flow.
- Reduced the basic catalog to core Developer, Games, and AI setup items; expanded tools now live in the optional catalog.
- Updated the elevated Chocolatey wrapper to wait for installs and return the installer exit code.
- Refreshed README setup and GUI documentation.

## [0.1.0] - 2026-05-17

### Added

- Added `setup/BasicSetupLauncher.ps1`, a Windows launcher with optional Git-based auto-update support.
- Added pytest coverage for configuration validity and installer command routing.
- Added project documentation in `README.md`.
- Added a tag-based GitHub Actions release workflow.

### Changed

- Modernized Linux distribution detection by reading `/etc/os-release` instead of using the removed `platform.linux_distribution()` API.
- Updated installer command execution to use explicit argument lists and `check=True`.
- Added Linux package manager handling for snap, apt, dnf, and yum.
- Normalized software catalog names for `Helm` and `Tilt`.
- Fixed the `Biznoe` profile reference for `7Zip`.

### Fixed

- Fixed Slack's Linux package value.
- Fixed package catalog entries with trailing whitespace that caused setup profile mismatches.
