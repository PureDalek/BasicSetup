from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch
from subprocess import CompletedProcess


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SETUP_DIRECTORY = REPOSITORY_ROOT / "setup"
SOFTWARE_CONFIG_PATH = SETUP_DIRECTORY / "software.json"
OPTIONAL_CATALOG_PATH = SETUP_DIRECTORY / "catalog_extra.json"
BLUEPRINT_CONFIG_PATH = SETUP_DIRECTORY / "blueprint.config"
VERSION_PATH = REPOSITORY_ROOT / "VERSION"


def load_json_config(config_path: Path) -> dict:
    """Load a JSON config file from disk."""
    with config_path.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def test_software_json_is_valid() -> None:
    """Verify the software catalog is valid JSON."""
    software_catalog = load_json_config(SOFTWARE_CONFIG_PATH)

    assert isinstance(software_catalog, dict)
    assert software_catalog


def test_optional_catalog_json_is_valid() -> None:
    """Verify the optional software catalog is valid JSON."""
    optional_catalog = load_json_config(OPTIONAL_CATALOG_PATH)

    assert isinstance(optional_catalog, dict)
    assert "RustDesk" in optional_catalog
    assert "Lens" in optional_catalog


def test_blueprint_config_is_valid() -> None:
    """Verify the setup blueprint file is valid JSON."""
    setup_blueprints = load_json_config(BLUEPRINT_CONFIG_PATH)

    assert isinstance(setup_blueprints, dict)
    assert setup_blueprints


def test_version_file_is_available() -> None:
    """Verify releases have a visible application version for the GUI."""
    version = VERSION_PATH.read_text(encoding="utf-8").strip()

    version_parts = version.split(".")
    assert len(version_parts) == 3
    assert all(part.isdigit() for part in version_parts)


def test_all_blueprint_packages_exist_in_software_catalog() -> None:
    """Verify every package referenced by a setup profile exists in a catalog."""
    software_catalog = load_json_config(SOFTWARE_CONFIG_PATH)
    optional_catalog = load_json_config(OPTIONAL_CATALOG_PATH)
    combined_catalog = {**software_catalog, **optional_catalog}
    setup_blueprints = load_json_config(BLUEPRINT_CONFIG_PATH)

    missing_packages_by_profile: dict[str, list[str]] = {}

    for profile_name, package_names in setup_blueprints.items():
        missing_packages = [
            package_name
            for package_name in package_names
            if package_name not in combined_catalog
        ]

        if missing_packages:
            missing_packages_by_profile[profile_name] = missing_packages

    assert missing_packages_by_profile == {}


def test_core_setup_profiles_are_available() -> None:
    """Verify the GUI exposes the expected first-run profile choices."""
    setup_blueprints = load_json_config(BLUEPRINT_CONFIG_PATH)

    for profile_name in ("Developer", "Games", "AI"):
        assert profile_name in setup_blueprints


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


def test_all_optional_catalog_entries_have_required_package_fields() -> None:
    """Verify optional catalog packages have both Windows and Linux package keys."""
    optional_catalog = load_json_config(OPTIONAL_CATALOG_PATH)

    malformed_packages: dict[str, list[str]] = {}

    for package_name, package_config in optional_catalog.items():
        missing_fields = [
            required_field
            for required_field in ("windows_package", "linux_package")
            if required_field not in package_config
        ]

        if missing_fields:
            malformed_packages[package_name] = missing_fields

    assert malformed_packages == {}


def test_program_setup_loaders_use_script_directory_paths() -> None:
    """Verify GUI config loading is independent of the caller's working directory."""
    sys.path.insert(0, str(SETUP_DIRECTORY))

    import program_setup

    software_catalog = program_setup.load_software_catalog()
    setup_profiles = program_setup.load_profiles()

    assert "Visual Studio Code" in software_catalog
    assert "Games" in setup_profiles


def test_program_setup_loads_application_version() -> None:
    """Verify the GUI can load the tracked app version."""
    sys.path.insert(0, str(SETUP_DIRECTORY))

    import program_setup

    assert program_setup.load_application_version() == VERSION_PATH.read_text(encoding="utf-8").strip()


def test_program_setup_update_channels_map_to_expected_branches() -> None:
    """Verify GUI update channel choices target the intended Git branches."""
    sys.path.insert(0, str(SETUP_DIRECTORY))

    import program_setup

    assert program_setup.update_channel_branch("Stable") == "main"
    assert program_setup.update_channel_branch("Nightly").startswith("codex/")
    assert program_setup.update_channel_branch("Unknown") == "main"


def test_program_setup_relaunch_preserves_dry_run_flag() -> None:
    """Verify update restart launches the GUI again with dry-run preserved."""
    sys.path.insert(0, str(SETUP_DIRECTORY))

    import program_setup

    with patch.object(program_setup.subprocess, "Popen") as popen_mock:
        program_setup.relaunch_application(dry_run=True)

    command_arguments = popen_mock.call_args.args[0]
    assert command_arguments[-1] == "--dry-run"
    assert command_arguments[-2].endswith("program_setup.py")


def test_program_setup_publishes_profile_changes_to_git() -> None:
    """Verify profile publishing stages only profile JSON, commits, and pushes."""
    sys.path.insert(0, str(SETUP_DIRECTORY))

    import program_setup

    calls: list[list[str]] = []

    def fake_run_git_command(arguments: list[str]) -> CompletedProcess[str]:
        calls.append(arguments)
        if arguments[:3] == ["status", "--porcelain", "--"]:
            return CompletedProcess(args=arguments, returncode=0, stdout=" M setup/blueprint.config\n", stderr="")
        if arguments == ["branch", "--show-current"]:
            return CompletedProcess(args=arguments, returncode=0, stdout="codex/test\n", stderr="")

        return CompletedProcess(args=arguments, returncode=0, stdout="", stderr="")

    with (
        patch.object(program_setup.shutil, "which", return_value="git"),
        patch.object(program_setup, "run_git_command", side_effect=fake_run_git_command),
    ):
        status, detail = program_setup.publish_profiles_to_git("My PC")

    assert status == "Published"
    assert "My PC" in detail
    assert ["add", str(program_setup.BLUEPRINT_CONFIG_PATH)] in calls
    assert ["commit", "-m", "Save setup profile My PC", "--", str(program_setup.BLUEPRINT_CONFIG_PATH)] in calls
    assert ["push", "-u", "origin", "codex/test"] in calls


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


def test_windows_installed_check_uses_chocolatey_local_package_list() -> None:
    """Verify Windows installed checks query Chocolatey's local package inventory."""
    sys.path.insert(0, str(SETUP_DIRECTORY))

    import software_installer
    from software_installer import SoftwareInstaller

    installer = SoftwareInstaller(
        software_name="git",
        windows_package="git",
        linux_package="git",
    )

    completed_process = software_installer.subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="git|2.51.0\n",
        stderr="",
    )

    with (
        patch.object(software_installer.platform, "system", return_value="Windows"),
        patch.object(software_installer.shutil, "which", return_value="C:\\ProgramData\\chocolatey\\bin\\choco.exe"),
        patch.object(installer, "_run_command_for_output", return_value=completed_process) as run_command_mock,
    ):
        assert installer.is_installed() is True

    run_command_mock.assert_called_once_with(
        ["choco", "list", "--local-only", "--exact", "git", "--limit-output"]
    )


def test_windows_installed_check_strips_package_arguments() -> None:
    """Verify package options do not become part of the Chocolatey lookup id."""
    sys.path.insert(0, str(SETUP_DIRECTORY))

    import software_installer
    from software_installer import SoftwareInstaller

    installer = SoftwareInstaller(
        software_name="Gimp",
        windows_package="gimp --version=2.10.4",
        linux_package="gimp",
    )

    completed_process = software_installer.subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="gimp|2.10.4\n",
        stderr="",
    )

    with (
        patch.object(software_installer.platform, "system", return_value="Windows"),
        patch.object(software_installer.shutil, "which", return_value="C:\\ProgramData\\chocolatey\\bin\\choco.exe"),
        patch.object(installer, "_run_command_for_output", return_value=completed_process) as run_command_mock,
    ):
        assert installer.is_installed() is True

    command_arguments = run_command_mock.call_args.args[0]
    assert command_arguments[4] == "gimp"
