# Elevate.ps1
param (
    [String]$PackageName
)
$process = Start-Process "choco" -ArgumentList "install $PackageName -y" -Verb RunAs -Wait -PassThru
exit $process.ExitCode
