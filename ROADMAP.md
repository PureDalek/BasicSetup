# BasicSetup Improvement Ideas

These are practical next steps that fit the current project shape.

## Catalog editing

- Add an "Add from catalog" workflow after the install/check flow is stable.
- Start with a local form that validates required fields before writing to `setup/software.json`.
- Validate package IDs by running package-manager search commands before saving.
- Keep a dry-run preview that shows the exact JSON diff before changing files.

## Git-backed saves

- Save catalog/profile changes through a branch-and-PR workflow instead of writing directly to `main`.
- After editing `software.json` or `blueprint.config`, run config tests, commit the JSON change, push the branch, and open a PR.
- Store a short change note with each catalog entry so future users know why it was added.

## Versioning

- Update `VERSION` for each release-worthy GUI or installer change.
- Use tags that match `VERSION`, for example `v0.2.0`.
- Show both the release version and Git commit in the GUI so support/debugging reports identify the exact build.

## Safer installs

- Add a pre-install summary that separates already-installed, installable, and manual packages.
- Add retry support for failed packages.
- Export install results to a timestamped log file.

## Package manager support

- Prefer package-manager native IDs over display names.
- Consider adding winget metadata for Windows alongside Chocolatey metadata.
- Add package-source fields so a package can be installed from Chocolatey, winget, a direct URL, or manually.
