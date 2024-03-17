#software_installer.py
import subprocess
import platform
import sys

class SoftwareInstaller:
    def __init__(self, software_name, windows_package, linux_package,linux_repo=None):
        self.software_name = software_name
        self.windows_package = windows_package
        self.linux_package = linux_package
        self.linux_repo = linux_repo

    def add_linux_repo(self):
        """Add a repository for Linux installations."""
        if self.linux_repo:
            print(f"Adding repository for {self.software_name}: {self.linux_repo}")
            subprocess.run(f"sudo add-apt-repository -y {self.linux_repo}", shell=True)
            subprocess.run("sudo apt-get update", shell=True)


    def install(self):
        """Install the software using the appropriate package manager."""
        if platform.system() == "Windows":
            subprocess.run(f"choco install {self.windows_package} -y", shell=True)
        elif platform.system() == "Linux":
            dist_name, _, _ = platform.linux_distribution()
            if "Ubuntu" in dist_name or "Debian" in dist_name:
                self.add_linux_repo()
                subprocess.run(f"sudo apt-get install {self.linux_package} -y", shell=True)
            elif "Fedora" in dist_name or "RedHat" in dist_name:
                subprocess.run(f"sudo yum install {self.linux_package} -y", shell=True)
            else:
                print(f"Unsupported Linux distribution: {dist_name}")
                sys.exit(1)
        else:
            print("Unsupported operating system.")
            sys.exit(1)
