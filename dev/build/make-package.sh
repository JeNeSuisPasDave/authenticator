#! /bin/bash
#
SCRIPTNAME_="$0"

# Get the directory holding this script
# (method from: http://stackoverflow.com/a/12694189/1392864)
#
SCRIPTDIR_="${BASH_SOURCE%/*}"
if [[ ! -d "$SCRIPTDIR_" ]]; then SCRIPTDIR_="$PWD"; fi

pushd src > /dev/null

# Build the distributions
#
python setup.py sdist bdist_wheel
# python setup.py --help
# python setup.py --verbose --dry-run sdist

popd > /dev/null