#! /bin/bash
#
SCRIPTNAME_="$0"

# Get the directory holding this script
# (method from: http://stackoverflow.com/a/12694189/1392864)
#
SCRIPTDIR_="${BASH_SOURCE%/*}"
if [[ ! -d "$SCRIPTDIR_" ]]; then SCRIPTDIR_="$PWD"; fi

pushd src > /dev/null

# Register the project
#
twine register -r pypi dist/authenticator-1.1.2.tar.gz
twine register -r pypi dist/authenticator-1.1.2-py3-none-any.whl

popd > /dev/null