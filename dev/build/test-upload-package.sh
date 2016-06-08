#! /bin/bash
#
SCRIPTNAME_="$0"

# Get the directory holding this script
# (method from: http://stackoverflow.com/a/12694189/1392864)
#
SCRIPTDIR_="${BASH_SOURCE%/*}"
if [[ ! -d "$SCRIPTDIR_" ]]; then SCRIPTDIR_="$PWD"; fi

pushd src > /dev/null

# upload the project
#
twine upload -r pypitest dist/*
# python setup.py sdist upload -r https://testpypi.python.org/pypi
# python setup.py bdist_wheel upload -r https://testpypi.python.org/pypi

popd > /dev/null