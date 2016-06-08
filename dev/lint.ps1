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
. "$scriptDir_\venv\check-functions.src.ps1"

# Check that we are running in a Python 3.5 virtual environment
#
. "$scriptDir_\venv\check-active-venv.src.ps1"
If (0 -ne $errcode_) {
  Exit
}

# Check that we have the needed packages
#
# We need: flake8, pep8-naming, pep257
#
. "$scriptDir_\venv\check-dependencies.src.ps1"
If (0 -ne $errcode_) {
  Exit
}

<#
.SYNOPSIS
Counts the errors recorded in a lint output file.
.DESCRIPTION
Given a file path, this function counts the number of errors or warnings
recorded in the file.
.PARAMETER LintOutputFile
A string containing the lint output file path.
.INPUTS
System.String. A string containing the line output file path.
.OUTPUTS
An integer count of the number of errors or warnings found in the lint
output file.
#>
Function Count-LintErrors {
    [CmdletBinding()]
    param(
        [Parameter(
            Mandatory=$True,
            ValueFromPipeline=$True,
            Position=0)]
        # See http://stackoverflow.com/a/6409122 for AllowEmptyString() tip
        [AllowEmptyString()]
        [string]$LintOutputFile
    )
    $count = $(
        Select-String "\.py\:[0-9]+\:" "$LintOutputFile" |
        Measure-Object -Line ).Lines

    # Get out
    #
    return $count
}

# lint the source
#
$env:PYTHONPATH="$pwd\src"
#
Push-Location ".\src\authenticator"
$rcmd = "flake8"
$rargs = "--exclude=ez_setup.py --max-complexity=10 ." -split " "
& $rcmd $rargs | Out-File fixme.lint.txt 2>&1
$rcmd = "pep257"
$rargs = "--match='(?!ez_setup).*\.py' ." -split " "
& $rcmd $rargs | Out-File -Append fixme.lint.txt 2>&1
$errorCount_ = Count-LintErrors "fixme.lint.txt"
If (0 -eq $errorCount_) {
    Write-Host ".\src\authenticator is OK" -ForegroundColor Green
}
Else {
    Write-Host ".\src\authenticator has $errorCount_ issues." `
        -ForegroundColor Red
}
Pop-Location
#
Push-Location ".\tests"
$rcmd = "flake8"
$rargs = "--max-complexity=10 ." -split " "
& $rcmd $rargs | Out-File fixme.lint.txt 2>&1
$rcmd = "pep257"
$rargs = "--match='(?!ez_setup).*\.py' ." -split " "
& $rcmd $rargs | Out-File -Append fixme.lint.txt 2>&1
$errorCount_ = Count-LintErrors "fixme.lint.txt"
If (0 -eq $errorCount_) {
    Write-Host ".\tests is OK" -ForegroundColor Green
}
Else {
    Write-Host ".\tests has $errorCount_ issues." `
        -ForegroundColor Red
}
Pop-Location
