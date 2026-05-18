# software_installer.py
from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path
from typing import Optional


SCRIPT_DIRECTORY = Path(__file__).resolve().parent


class SoftwareInstaller:
    """Install a configured software package for the current operating system."""

    def __init__(
        self,
        software_name: str,
        windows_package: Optional[str],
        linux_package: Optional[str],
        linux_repo: Optional[str] = None,
        is_snap: bool = False,
        from_site: Optional[str] = None,
    ) -> None:
        self.software_name = software_name
        self.windows_package = windows_package
        self.linux_package = linux_package
        self.linux_repo = linux_repo
        self.is_snap = is_snap
        self.from_site = from_site

    @staticmethod
    def _run_command(command_arguments: list[str]) -> None:
        """Run a command and fail loudly when the command does not succeed."""
        try:
            subprocess.run(command_arguments, check=True)
        except FileNotFoundError as error:
            command_name = command_arguments[0]
            raise RuntimeError(f"Required command was not found: {command_name}") from error
        except subprocess.CalledProcessError as error:
            command_text = " ".join(command_arguments)
            raise RuntimeError(f"Command failed with exit code {error.returncode}: {command_text}") from error

    @staticmethod
    def _run_command_for_output(command_arguments: list[str]) -> subprocess.CompletedProcess[str]:
        """Run a command and return captured output without raising on non-zero exit codes."""
        try:
            return subprocess.run(
                command_arguments,
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as error:
            command_name = command_arguments[0]
            raise RuntimeError(f"Required command was not found: {command_name}") from error

    @staticmethod
    def _package_id(package_name: Optional[str]) -> Optional[str]:
        """Return the package id without installer-specific command arguments."""
        if not package_name:
            return None

        return package_name.split()[0]

    @staticmethod
    def _read_linux_distribution_info() -> dict[str, str]:
        """Read Linux distribution metadata from /etc/os-release."""
        os_release_path = Path("/etc/os-release")
        distribution_info: dict[str, str] = {}

        if not os_release_path.exists():
            return distribution_info

        for raw_line in os_release_path.read_text(encoding="utf-8").splitlines():
            if "=" not in raw_line or raw_line.startswith("#"):
                continue

            key, value = raw_line.split("=", 1)
            distribution_info[key.lower()] = value.strip().strip('"').lower()

        return distribution_info

    @classmethod
    def _is_debian_like_distribution(cls) -> bool:
        """Return whether the current Linux distribution uses apt packages."""
        distribution_info = cls._read_linux_distribution_info()
        distribution_id = distribution_info.get("id", "")
        distribution_family = distribution_info.get("id_like", "")

        return distribution_id in {"debian", "ubuntu"} or "debian" in distribution_family

    @classmethod
    def _is_fedora_like_distribution(cls) -> bool:
        """Return whether the current Linux distribution uses dnf or yum packages."""
        distribution_info = cls._read_linux_distribution_info()
        distribution_id = distribution_info.get("id", "")
        distribution_family = distribution_info.get("id_like", "")

        fedora_like_ids = {"fedora", "rhel", "redhat", "centos", "rocky", "almalinux"}
        return distribution_id in fedora_like_ids or any(
            family_name in distribution_family
            for family_name in ("fedora", "rhel", "redhat")
        )

    def _install_windows_package(self) -> None:
        """Install the Windows package through the elevated Chocolatey wrapper."""
        if not self.windows_package:
            raise ValueError(f"No Windows package configured for {self.software_name}")

        elevate_script_path = SCRIPT_DIRECTORY / "Elevate.ps1"

        self._run_command(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(elevate_script_path),
                self.windows_package,
            ]
        )

    def _is_windows_package_installed(self) -> bool:
        """Return whether the Chocolatey package is already installed."""
        package_id = self._package_id(self.windows_package)
        if not package_id or not shutil.which("choco"):
            return False

        result = self._run_command_for_output(
            ["choco", "list", "--local-only", "--exact", package_id, "--limit-output"]
        )
        if result.returncode != 0:
            return False

        return any(line.lower().startswith(f"{package_id.lower()}|") for line in result.stdout.splitlines())

    def _add_linux_repo(self) -> None:
        """Add an apt repository before installing a package."""
        if not self.linux_repo:
            return

        print(f"Adding repository for {self.software_name}: {self.linux_repo}")
        self._run_command(["sudo", "add-apt-repository", "-y", self.linux_repo])
        self._run_command(["sudo", "apt-get", "update"])

    def _install_linux_package(self) -> None:
        """Install the Linux package through snap, apt, dnf, or yum."""
        if not self.linux_package:
            if self.from_site:
                print(f"{self.software_name} must be installed manually from: {self.from_site}")
                return

            raise ValueError(f"No Linux package configured for {self.software_name}")

        if self.is_snap:
            self._run_command(["sudo", "snap", "install", self.linux_package])
            return

        if self._is_debian_like_distribution():
            self._add_linux_repo()
            self._run_command(["sudo", "apt-get", "install", self.linux_package, "-y"])
            return

        if self._is_fedora_like_distribution():
            package_manager = "dnf" if shutil.which("dnf") else "yum"
            self._run_command(["sudo", package_manager, "install", self.linux_package, "-y"])
            return

        distribution_info = self._read_linux_distribution_info()
        distribution_name = distribution_info.get("name", "unknown Linux distribution")
        raise RuntimeError(f"Unsupported Linux distribution: {distribution_name}")

    def _is_linux_package_installed(self) -> bool:
        """Return whether the configured Linux package appears to be installed."""
        package_id = self._package_id(self.linux_package)
        if not package_id:
            return False

        if self.is_snap and shutil.which("snap"):
            result = self._run_command_for_output(["snap", "list", package_id])
            return result.returncode == 0

        if self._is_debian_like_distribution() and shutil.which("dpkg-query"):
            result = self._run_command_for_output(["dpkg-query", "-W", "-f=${Status}", package_id])
            return result.returncode == 0 and "install ok installed" in result.stdout

        if self._is_fedora_like_distribution() and shutil.which("rpm"):
            result = self._run_command_for_output(["rpm", "-q", package_id])
            return result.returncode == 0

        return False

    def install(self) -> None:
        """Install the software using the appropriate package manager."""
        current_operating_system = platform.system()

        if current_operating_system == "Windows":
            self._install_windows_package()
            return

        if current_operating_system == "Linux":
            self._install_linux_package()
            return

        raise RuntimeError(f"Unsupported operating system: {current_operating_system}")

    def is_installed(self) -> bool:
        """Return whether the configured package appears to be installed on this machine."""
        current_operating_system = platform.system()

        if current_operating_system == "Windows":
            return self._is_windows_package_installed()

        if current_operating_system == "Linux":
            return self._is_linux_package_installed()

        return False
