from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SETUP_DIRECTORY = REPOSITORY_ROOT / "setup"
SOFTWARE_CONFIG_PATH = SETUP_DIRECTORY / "software.json"
BLUEPRINT_CONFIG_PATH = SETUP_DIRECTORY / "blueprint.config"


def load_json_config(config_path: Path) -> dict:
    """Load a JSON config file from disk."""
    with config_path.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def test_software_json_is_valid() -> None:
    """Verify the software catalog is valid JSON."""
    software_catalog = load_json_config(SOFTWARE_CONFIG_PATH)

    assert isinstance(software_catalog, dict)
    assert software_catalog


def test_blueprint_config_is_valid() -> None:
    """Verify the setup blueprint file is valid JSON."""
    setup_blueprints = load_json_config(BLUEPRINT_CONFIG_PATH)

    assert isinstance(setup_blueprints, dict)
    assert setup_blueprints


def test_all_blueprint_packages_exist_in_software_catalog() -> None:
    """Verify every package referenced by a setup profile exists in software.json."""
    software_catalog = load_json_config(SOFTWARE_CONFIG_PATH)
    setup_blueprints = load_json_config(BLUEPRINT_CONFIG_PATH)

    missing_packages_by_profile: dict[str, list[str]] = {}

    for profile_name, package_names in setup_blueprints.items():
        missing_packages = [
            package_name
            for package_name in package_names
            if package_name not in software_catalog
        ]

        if missing_packages:
            missing_packages_by_profile[profile_name] = missing_packages

    assert missing_packages_by_profile == {}


def test_software_catalog_keys_do_not_have_extra_whitespace() -> None:
    """Prevent subtle config mismatches caused by leading or trailing spaces."""
    software_catalog = load_json_config(SOFTWARE_CONFIG_PATH)

    invalid_package_names = [
        package_name
        for package_name in software_catalog
        if package_name != package_name.strip()
    ]

    assert invalid_package_names == []


def test_all_software_entries_have_required_package_fields() -> None:
    """Verify every package has both Windows and Linux package keys."""
    software_catalog = load_json_config(SOFTWARE_CONFIG_PATH)

    malformed_packages: dict[str, list[str]] = {}

    for package_name, package_config in software_catalog.items():
        missing_fields = [
            required_field
            for required_field in ("windows_package", "linux_package")
            if required_field not in package_config
        ]

        if missing_fields:
            malformed_packages[package_name] = missing_fields

    assert malformed_packages == {}


def test_linux_installer_uses_snap_for_snap_packages() -> None:
    """Verify Linux snap packages call snap instead of apt."""
    sys.path.insert(0, str(SETUP_DIRECTORY))

    import software_installer
    from software_installer import SoftwareInstaller

    installer = SoftwareInstaller(
        software_name="Slack",
        windows_package="slack",
        linux_package="slack",
        is_snap=True,
    )

    with (
        patch.object(software_installer.platform, "system", return_value="Linux"),
        patch.object(installer, "_run_command") as run_command_mock,
    ):
        installer.install()

    run_command_mock.assert_called_once_with(["sudo", "snap", "install", "slack"])


def test_windows_installer_uses_elevated_powershell_wrapper() -> None:
    """Verify Windows packages are installed through the PowerShell wrapper."""
    sys.path.insert(0, str(SETUP_DIRECTORY))

    import software_installer
    from software_installer import SoftwareInstaller

    installer = SoftwareInstaller(
        software_name="git",
        windows_package="git",
        linux_package="git",
    )

    with (
        patch.object(software_installer.platform, "system", return_value="Windows"),
        patch.object(installer, "_run_command") as run_command_mock,
    ):
        installer.install()

    command_arguments = run_command_mock.call_args.args[0]
    assert command_arguments[:5] == [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
    ]
    assert command_arguments[-1] == "git"
