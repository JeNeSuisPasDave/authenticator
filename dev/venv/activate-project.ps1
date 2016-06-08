# A script to activate the local version of Ruby
#
Set-Strictmode -version Latest

# Capture the file name of this powershell script
#
$scriptName = $MyInvocation.InvocationName
$scriptDir = $PSScriptRoot
$cwd = (Get-Item -Path ".\" -Verbose).FullName

# Set error code
#
$errorcode = 0

# Check that Python exists
#
$pylclDir = "venv35"
$pyBinPath = "$cwd\$pylclDir\Scripts"
If (-not (Test-Path "$pyBinPath\python.exe")) {
    Write-Output ""
    Write-Output "ERROR: Python is not installed in '.\$pylclDir'."
    Write-Output "Cannot activate Python virtual environment."
    Write-Output ""
    Exit
}

# Activate Python
#
& "$pyBinPath\Activate.ps1"

# Set the deactivation script
#
$deactivateFile = $scriptDir + "\deactivate-project.ps1"
"deactivate" | Out-File $deactivateFile -Width 256
"Remove-Item `"$deactivateFile`"" |
    Out-File $deactivateFile -Append -Width 256

# Get out
#
Write-Output ""
Write-Output "The Python virtual environment is activated."
Write-Output "To deactivate it, run '$deactivateFile'."
Write-Output ""
