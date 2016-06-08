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

$venvDirName_ = "venv35"
$save_venvDirName_ = "$venvDirName_" + "_bkup"
$pythonVersion_ = "3.5"
$pythonInstallbase_ = "C:\Program Files\Python $pythonVersion_"

# Check whether Python 3.5 is installed
#
$pythonInstalled_ = Get-ChildItem "$pythonInstallbase_" |
  Where-Object {($_.Name -eq "python.exe")}
If ($pythonInstalled_ -eq $null)
{
  Write-Output ""
  Write-Output "ERROR: Python 3.5 is not installed."
  Write-Output "       Expected '$pythonInstallbase_\python.exe'"
  Write-Output "Install Python 3.5 and then try '.\$scriptName_' again."
  Exit
}

# Check whether we are running in a python virtual environment
#
$venvRunning_ = Get-ChildItem env: | Where-Object {($_.Name -eq "VIRTUAL_ENV")}
If ($venvRunning_ -ne $null)
{
  Write-Output ""
  Write-Output "ERROR: Python virtual environment already running"
  Write-Output ""
  Write-Output "Try 'deactivate' to stop the virtual environment, and"
  Write-Output "then try '.\$scriptName_' again."
  Write-Output ""
  Exit
}

# Check whether the virtual environment directory already exists
#
If (Test-Path ".\$venvDirName_")
{
  Write-Output ""
  Write-Output ("WARNING: virtual environment directory '.\$venvDirName_' " `
    + "already exists.")
  $yesno_ = Read-Host "Do you want to delete and replace it? [y/N]"
  if ($yesno_ -ne 'y')
  {
    Write-Output "No action taken."
    Exit
  }
  # Rename the existing directory
  #
  Move-Item ".\$venvDirName_" ".\$save_venvDirName_"
}

# Create the virtual environment directory (the deployment folder)
#
& "$pythonInstallbase_\python.exe" -m venv "$venvDirName_"
If (Test-Path ".\$venvDirName_")
{
  If (Test-Path ".\$save_venvDirName_")
  {
    Remove-Item -Recurse ".\$save_venvDirName_"
  }
}
else
{
  Write-Output "ERROR: virtual environment not created."
  If (Test-Path ".\$save_venvDirName_")
  {
    Move-Item ".\$save_venvDirName_" ".\$venvDirName_"
  }
  Exit
}

# Activate the virtual environment
#
& .\$venvDirName_\Scripts\Activate.ps1

# Check whether we are running in a python virtual environment
#
$venvRunning_ = Get-ChildItem env: | Where-Object {($_.Name -eq "VIRTUAL_ENV")}
If ($venvRunning_ -eq $null)
{
  Write-Output ("ERROR: Python virtual environment was not activated; " `
    + " not running")
  Exit
}

# Check whether we are running Python 3.5
#
$rcmd_ = "python"
$rargs_ = "--version 2>&1" -split " "
$vsn_ = Invoke-Expression "$rcmd_ $rargs_"
if ($vsn_ -NotLike "Python 3.*")
{
  Write-Output "ERROR: Python 3.5 or later is required. Found '$vsn'."
  Write-Output ""
  Write-Output "Deactivate the current virtual environment."
  Write-Output ("Try '.\$venvDirName_\Scripts\Activate.ps1' to start the " `
    + "virtual environment, and")
  Write-Output "then try '.\$scriptName_' again."
  Write-Output ""
  Exit
}

# Update setuptools and pip
#
python -m pip install -q --upgrade pip
python -m pip install -q --upgrade setuptools

# deactivate the virtual environment
#
deactivate

# Done!
#
Write-Output ""
Write-Output "OK. Virtual environment for Python 3.5 is created."
Write-Output "Use command '.\$venvDirName_\Scripts\Activate.ps1' to start;"
Write-Output "Use command 'deactivate' to stop."
Write-Output ""
