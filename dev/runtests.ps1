# Run the automated tests
#
Set-Strictmode -version Latest

# Capture the file name of this powershell script
#
$SCRIPTNAME_ = $MyInvocation.InvocationName

$scriptDir_ = $PSScriptRoot

# Set error code
#
$errcode_ = 0

# Pick up the verification functions
#
. "$scriptDir_\venv\check-functions.src.ps1"

# Check that we are running in a Python 3.5 virtual environment
#
. "$scriptDir_\venv\check-active-venv.src.ps1"
If (0 -ne $errcode_) {
  Exit
}

# Check that we have the needed packages
#
. "$scriptDir_\venv\check-dependencies.src.ps1"
If (0 -ne $errcode_) {
  Exit
}

# Run the test
#
$env:PYTHONPATH="$pwd\src"
$rcmd = "python"
$rargs = "-m unittest discover -s ./tests" -Split " "
& $rcmd $rargs
