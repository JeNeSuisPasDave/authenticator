# NOTE: expect that this is preceded by source command:
# . check-functions.ps1
#

# pip install cryptography, iso8601
#
#
$cffiExpectedVsn_ = Extract-Version "1.6.0"
$cffiMaxVsn_ = Extract-Version "1.6.1"
$cryptographyExpectedVsn_ = Extract-Version "1.4"
$cryptographyMaxVsn_ = Extract-Version "1.5"
$idnaExpectedVsn_ = Extract-Version "2.1"
$idnaMaxVsn_ = Extract-Version "2.2"
$iso8601ExpectedVsn_ = Extract-Version "0.1.11"
$iso8601MaxVsn_ = Extract-Version "0.1.12"
$pyasn1ExpectedVsn_ = Extract-Version "0.1.9"
$pyasn1MaxVsn_ = Extract-Version "0.1.10"
$pycparserExpectedVsn_ = Extract-Version "2.14"
$pycparserMaxVsn_ = Extract-Version "2.15"
$sixExpectedVsn_ = Extract-Version "1.10.0"
$sixMaxVsn_ = Extract-Version "1.10.1"

# For linting
#
$flake8ExpectedVsn_ = Extract-Version "2.5.4"
$flake8MaxVsn_ = Extract-Version "2.5.5"
$mccabeExpectedVsn_ = Extract-Version "0.4.0"
$mccabeMaxVsn_ = Extract-Version "0.4.1"
$pep257ExpectedVsn_ = Extract-Version "0.7.0"
$pep257MaxVsn_ = Extract-Version "0.7.1"
$pep8ExpectedVsn_ = Extract-Version "1.7.0"
$pep8MaxVsn_ = Extract-Version "1.7.1"
$pep8namingExpectedVsn_ = Extract-Version "0.3.3"
$pep8namingMaxVsn_ = Extract-Version "0.3.4"
$pyflakesExpectedVsn_ = Extract-Version "1.0.0"
$pyflakesMaxVsn_ = Extract-Version "1.0.1"

# For creating PyPI packages
#
$pkginfoExpectedVsn_ = Extract-Version "1.3.2"
$pkginfoMaxVsn_ = Extract-Version "1.3.3"
$requestsExpectedVsn_ = Extract-Version "2.10.0"
$requestsMaxVsn_ = Extract-Version "2.10.1"
$requeststoolbeltExpectedVsn_ = Extract-Version "0.6.2"
$requeststoolbeltMaxVsn_ = Extract-Version "0.6.3"
$twineExpectedVsn_ = Extract-Version "1.6.5"
$twineMaxVsn_ = Extract-Version "1.6.6"
$wheelExpectedVsn_ = Extract-Version "0.29.0"
$wheelMaxVsn_ = Extract-Version "0.29.1"

# For creating EXE packages
#
$pyinstallerExpectedVsn_ = Extract-Version "3.2.0"
$pyinstallerMaxVsn_ = Extract-Version "3.2.1"

<#
.SYNOPSIS
Check whether the Python package is installed and, if so, whether it is
within the range of versions specified.
.DESCRIPTION
Given a package name, this function checks whether such a package is
installed. If minimum and maximum versions are supplied, then this function
also checks whether the installed package is within that range [min, max).
.PARAMETER Name
A string containing the package name.
.PARAMETER MinVersion
System.String or an object containing Major, Minor, Patch, and Qualifier
members (as produced by the Extract-Version function). If supplied, the
installed version is expected to be greater than or equal to MinVersion.
.PARAMETER MaxVersion
System.String or an object containing Major, Minor, Patch, and Qualifier
members (as produced by the Extract-Version function). If supplied, the
installed version is expected to be less than MaxVersion.
.PARAMETER PipPackages
A list of pip packages produced by "pip list".
.INPUTS
System.String. A string containing a package name.
.OUTPUTS
System.Management.Automation.PSCustomObject. Properties are Installed (bool),
InRange (bool), FullVersion (System.Version).
#>
Function Check-DependentVersion {
    [CmdletBinding()]
    param(
        [Parameter(
            Mandatory=$True,
            ValueFromPipeline=$True,
            Position=0)]
        # See http://stackoverflow.com/a/6409122 for AllowEmptyString() tip
        [AllowEmptyString()]
        [string]$Name,
        [Parameter(
            Mandatory=$True,
            Position=1)]
        [PSObject]$MinVersion,
        [Parameter(
            Mandatory=$True,
            Position=2)]
        [PSObject]$MaxVersion,
        [Parameter(
            Mandatory=$True,
            Position=3)]
        [PSObject]$PipPackages
    )
    $msg = New-Object "System.Collections.Generic.List[String]"
    $chk_ = IsInstalled-PythonPackage -Name $Name -MinVersion `
        $MinVersion -MaxVersion $MaxVersion -PipPackages $PipPackages
    If (-not $chk_.Installed) {
        $msg.Add("")
        $msg.Add("ERROR: $Name is not installed")
        $msg.Add("")
        $msg.Add("Try '$scriptDir_\provision-venv.ps1' to install $Name, and" +
            "then try '$scriptName_' again.")
        $msg.Add("")
    } ElseIf (-not $chk_.InRange) {
        $mnv_ = ToString-Version $MinVersion
        $mxv_ = ToString-Version $MaxVersion
        $flv_ = ToString-Version $chk_.FullVersion
        $msg.Add("")
        $msg.Add("ERROR: Expecting $Name $mnv_ or later, " +
          "up to $mxv_.")
        $msg.Add("Found $flv_")
        $msg.Add("")
    }
    return , $msg
}

# Capture pip packages
#
$rcmd_ = "pip"
$rargs_ = "list" -split " "
$pkgs_ = Invoke-Expression "$rcmd_ $rargs_"

# Check whether cffi installed
#
$msg_ = Check-DependentVersion "cffi" -MinVersion $cffiExpectedVsn_ `
    -MaxVersion $cffiMaxVsn_ -PipPackages $pkgs_
If (0 -lt $msg_.Count) {
    Write-Output $( $msg_ -Join "`n" )
    $errcode_ = 8
    Exit
}

# Check whether cryptography installed
#
$msg_ = Check-DependentVersion "cryptography" `
    -MinVersion $cryptographyExpectedVsn_ `
    -MaxVersion $cryptographyMaxVsn_ -PipPackages $pkgs_
If (0 -lt $msg_.Count) {
    Write-Output $( $msg_ -Join "`n" )
    $errcode_ = 8
    Exit
}

# Check whether idna installed
#
$msg_ = Check-DependentVersion "idna" -MinVersion $idnaExpectedVsn_ `
    -MaxVersion $idnaMaxVsn_ -PipPackages $pkgs_
If (0 -lt $msg_.Count) {
    Write-Output $( $msg_ -Join "`n" )
    $errcode_ = 8
    Exit
}

# Check whether iso8601 installed
#
$msg_ = Check-DependentVersion "iso8601" -MinVersion $iso8601ExpectedVsn_ `
    -MaxVersion $iso8601MaxVsn_ -PipPackages $pkgs_
If (0 -lt $msg_.Count) {
    Write-Output $( $msg_ -Join "`n" )
    $errcode_ = 8
    Exit
}

# Check whether pyasn1 installed
#
$msg_ = Check-DependentVersion "pyasn1" -MinVersion $pyasn1ExpectedVsn_ `
    -MaxVersion $pyasn1MaxVsn_ -PipPackages $pkgs_
If (0 -lt $msg_.Count) {
    Write-Output $( $msg_ -Join "`n" )
    $errcode_ = 8
    Exit
}

# Check whether pycparser installed
#
$msg_ = Check-DependentVersion "pycparser" -MinVersion $pycparserExpectedVsn_ `
    -MaxVersion $pycparserMaxVsn_ -PipPackages $pkgs_
If (0 -lt $msg_.Count) {
    Write-Output $( $msg_ -Join "`n" )
    $errcode_ = 8
    Exit
}

# Check whether six installed
#
$msg_ = Check-DependentVersion "six" -MinVersion $sixExpectedVsn_ `
    -MaxVersion $sixMaxVsn_ -PipPackages $pkgs_
If (0 -lt $msg_.Count) {
    Write-Output $( $msg_ -Join "`n" )
    $errcode_ = 8
    Exit
}

# Check whether flake8 installed
#
$msg_ = Check-DependentVersion "flake8" -MinVersion $flake8ExpectedVsn_ `
    -MaxVersion $flake8MaxVsn_ -PipPackages $pkgs_
If (0 -lt $msg_.Count) {
    Write-Output $( $msg_ -Join "`n" )
    $errcode_ = 8
    Exit
}

# Check whether mccabe installed
#
$msg_ = Check-DependentVersion "mccabe" -MinVersion $mccabeExpectedVsn_ `
    -MaxVersion $mccabeMaxVsn_ -PipPackages $pkgs_
If (0 -lt $msg_.Count) {
    Write-Output $( $msg_ -Join "`n" )
    $errcode_ = 8
    Exit
}

# Check whether pep257 installed
#
$msg_ = Check-DependentVersion "pep257" -MinVersion $pep257ExpectedVsn_ `
    -MaxVersion $pep257MaxVsn_ -PipPackages $pkgs_
If (0 -lt $msg_.Count) {
    Write-Output $( $msg_ -Join "`n" )
    $errcode_ = 8
    Exit
}

# Check whether pep8 installed
#
$msg_ = Check-DependentVersion "pep8" -MinVersion $pep8ExpectedVsn_ `
    -MaxVersion $pep8MaxVsn_ -PipPackages $pkgs_
If (0 -lt $msg_.Count) {
    Write-Output $( $msg_ -Join "`n" )
    $errcode_ = 8
    Exit
}

# Check whether pep8-naming installed
#
$msg_ = Check-DependentVersion "pep8-naming" `
    -MinVersion $pep8namingExpectedVsn_ `
    -MaxVersion $pep8namingMaxVsn_ -PipPackages $pkgs_
If (0 -lt $msg_.Count) {
    Write-Output $( $msg_ -Join "`n" )
    $errcode_ = 8
    Exit
}

# Check whether pyflakes installed
#
$msg_ = Check-DependentVersion "pyflakes" -MinVersion $pyflakesExpectedVsn_ `
    -MaxVersion $pyflakesMaxVsn_ -PipPackages $pkgs_
If (0 -lt $msg_.Count) {
    Write-Output $( $msg_ -Join "`n" )
    $errcode_ = 8
    Exit
}

# Check whether pkginfo installed
#
$msg_ = Check-DependentVersion "pkginfo" -MinVersion $pkginfoExpectedVsn_ `
    -MaxVersion $pkginfoMaxVsn_ -PipPackages $pkgs_
If (0 -lt $msg_.Count) {
    Write-Output $( $msg_ -Join "`n" )
    $errcode_ = 8
    Exit
}

# Check whether requests installed
#
$msg_ = Check-DependentVersion "requests" -MinVersion $requestsExpectedVsn_ `
    -MaxVersion $requestsMaxVsn_ -PipPackages $pkgs_
If (0 -lt $msg_.Count) {
    Write-Output $( $msg_ -Join "`n" )
    $errcode_ = 8
    Exit
}

# Check whether requests-toolbelt installed
#
$msg_ = Check-DependentVersion "requests-toolbelt" `
    -MinVersion $requeststoolbeltExpectedVsn_ `
    -MaxVersion $requeststoolbeltMaxVsn_ -PipPackages $pkgs_
If (0 -lt $msg_.Count) {
    Write-Output $( $msg_ -Join "`n" )
    $errcode_ = 8
    Exit
}

# Check whether twine installed
#
$msg_ = Check-DependentVersion "twine" -MinVersion $twineExpectedVsn_ `
    -MaxVersion $twineMaxVsn_ -PipPackages $pkgs_
If (0 -lt $msg_.Count) {
    Write-Output $( $msg_ -Join "`n" )
    $errcode_ = 8
    Exit
}

# Check whether wheel installed
#
$msg_ = Check-DependentVersion "wheel" -MinVersion $wheelExpectedVsn_ `
    -MaxVersion $wheelMaxVsn_ -PipPackages $pkgs_
If (0 -lt $msg_.Count) {
    Write-Output $( $msg_ -Join "`n" )
    $errcode_ = 8
    Exit
}

# Check whether PyInstaller installed
#
$msg_ = Check-DependentVersion "PyInstaller" -MinVersion $pyinstallerExpectedVsn_ `
    -MaxVersion $pyinstallerMaxVsn_ -PipPackages $pkgs_
If (0 -lt $msg_.Count) {
    Write-Output $( $msg_ -Join "`n" )
    $errcode_ = 8
    Exit
}
