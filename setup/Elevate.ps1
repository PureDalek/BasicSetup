# Elevate.ps1
param (
    [String]$PackageName
)
Start-Process "choco" -ArgumentList "install $PackageName -y" -Verb RunAs
