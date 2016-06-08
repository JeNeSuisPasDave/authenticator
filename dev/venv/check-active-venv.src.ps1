# NOTE: expect that this is preceded by this source command:
# . check-functions.ps1
#

$venvDirname_ = "venv35"
$pythonExpectedVsn_ = Extract-Version "3.5.1"
$pythonMaxVsn_ = Extract-Version "3.6.0"

# Check whether we are running in a python virtual environment
#
If (-not (Test-Path Env:VIRTUAL_ENV)) {
  Write-Output ""
  Write-Output "ERROR: Python virtual environment not running"
  Write-Output ""
  Write-Output ("Try '.\dev\venv\activate-project.ps1' to start the " `
    + "virtual environment,")
  Write-Output "and then try '$scriptName_' again."
  Write-Output ""
  $errcode_ = 2
  Exit
}

# Check whether we are running Python 3.5
#
$pythonDownloadLoc_="https://www.python.org/"
$rcmd_ = "python"
$rargs_ = "--version 2>&1" -split " "
$vsn_ = Invoke-Expression "$rcmd_ $rargs_" | Extract-Version
If (!$vsn_) {
  Write-Output ""
  Write-Output "ERROR: Python is not installed or not in the path."
  Write-Output ""
  Write-Output "Install Python; perhaps from $pythonDownloadLoc_"
  Write-Output ""
  $errcode_ = 4
  Exit
}
If ((-not (Test-Version $vsn_ -IsAtLeast $pythonExpectedVsn_)) `
-or (-not (Test-Version $vsn_ -IsLessThan $pythonMaxVsn_))) {
  Write-Output ""
  Write-Output ("ERROR: Expecting Python $pythonExpectedVsn_ or later, " `
    + "up to $pythonMaxVsn_")
  Write-Output "Found $vsn_"
  Write-Output ""
  $errcode_ = 6
  Exit
}
