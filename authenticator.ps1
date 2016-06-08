# Check style and PEP compliance for source code
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
. "$scriptDir_\dev\venv\check-functions.src.ps1"

# Check that we are running in a Python 3.5 virtual environment
#
. "$scriptDir_\dev\venv\check-active-venv.src.ps1"
If (0 -ne $errcode_) {
  Exit
}

# Check that we have the needed packages
#
# We need: flake8, pep8-naming, pep257
#
. "$scriptDir_\dev\venv\check-dependencies.src.ps1"
If (0 -ne $errcode_) {
  Exit
}

# Run this from the root directory of the project
#
$allArgs_ = $PsBoundParameters.Values + $args
$env:PYTHONPATH="$pwd\src"
$rcmd = "python"
$rargs = $( "-m authenticator.cli" -Split " " ) + $allArgs_
& $rcmd $rargs
