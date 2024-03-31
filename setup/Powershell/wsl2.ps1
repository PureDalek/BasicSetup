# Enable WSL
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# Enable Virtual Machine Platform (required for WSL 2)
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Download and Install the Linux kernel update package for WSL 2
# Note: You might want to manually download and install the WSL2 kernel from the Microsoft website if this step fails
Invoke-WebRequest -Uri https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi -OutFile $env:TEMP/wsl_update_x64.msi
Start-Process msiexec.exe -Wait -ArgumentList '/i', $env:TEMP/wsl_update_x64.msi, '/quiet'

# Set WSL 2 as the default version
wsl --set-default-version 2
