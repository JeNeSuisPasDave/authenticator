# This script assumes that Python 3.5 is installed in
# C:\Program Files\Python 3.5
#
# If Python 3.5 is installed some other way, then the script will
# need some adjustment.
#
Set-Strictmode -version Latest

# Capture the file name of this powershell script
#
$scriptName_ = $MyInvocation.InvocationName

$scriptDir_ = $PSScriptRoot

# Set error code
#
$errcode_ = 0

# Pick up the verification functions
#
. "$scriptDir_\check-functions.src.ps1"

# Check that we are running in a Python 3.5 virtual environment
#
. "$scriptDir_\check-active-venv.src.ps1"
If (0 -ne $errcode_) {
  Exit
}

# Install required packages
#
$rcmd_ = "pip"
$rargs_ = "install -q -r `"$scriptDir_\requirements-venv.txt`"" -split " "
Invoke-Expression "$rcmd_ $rargs_"

# Check that we have the needed packages
#
. "$scriptDir_\check-dependencies.src.ps1"
If (0 -ne $errcode_) {
  Exit
}

# Done!
#
Write-Output ""
Write-Output ("OK. Provisioned required packages for project in " `
  + "Python 3.5 virtual environment.")
Write-Output ""
