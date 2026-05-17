# Changelog

All notable changes to BasicSetup will be documented in this file.

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
