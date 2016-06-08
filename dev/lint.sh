#! /bin/bash
#

# Run this from the root directory of the project
#

# Capture the file name of this bash script
#
SCRIPTNAME_=$0

# Check whether we are running in a python virtual environment
#
VENV_RUNNING_=`env | grep VIRTUAL_ENV | wc -l | tr -d [[:space:]]`
if [ 0 == ${VENV_RUNNING_} ]; then
  echo "ERROR: Python virtual environment not running"
  echo
  echo "Try '. venv35/bin/activate' to start the virtual environment, and"
  echo "then try '${SCRIPTNAME_}' again."
  echo
  exit 1
fi

# Check whether we are running Python 3
#
export PYVER_=`python --version 2>&1 | grep "^Python 3\." | wc -l | tr -d [[:space:]]`
if [ 0 == ${PYVER_} ]; then
  echo "ERROR: Python 3 is required. Found "`python --version`"."
  echo
  echo "Deactivate the current virtual environment."
  echo "Try '. venv35/bin/activate' to start the virtual environment, and"
  echo "then try '${SCRIPTNAME_}' again."
  echo
  exit 1
fi

# Check whether flake8 is installed
#
FLAKE8_INSTALLED_=`pip list | grep "^flake8 (" | wc -l | tr -d [[:space:]]`
if [ 0 == ${FLAKE8_INSTALLED_} ]; then
  echo "ERROR: flake8 is not installed"
  echo
  echo "Try 'pip install flake8' to install flake8, and"
  echo "then try '${SCRIPTNAME_}' again."
  echo
  exit 1
fi

# Check whether pep8-naming is installed
#
PEP8NAMING_INSTALLED_=`pip list | grep "^pep8-naming (" | wc -l | tr -d [[:space:]]`
if [ 0 == ${PEP8NAMING_INSTALLED_} ]; then
  echo "ERROR: pep8-naming is not installed"
  echo
  echo "Try 'pip install pep8-naming' to install pep8-naming, and"
  echo "then try '${SCRIPTNAME_}' again."
  echo
  exit 1
fi

# Check whether pep257 is installed
#
PEP257_INSTALLED_=`pip list | grep "^pep257 (" | wc -l | tr -d [[:space:]]`
if [ 0 == ${PEP257_INSTALLED_} ]; then
  echo "ERROR: pep257 is not installed"
  echo
  echo "Try 'pip install pep257' to install pep257, and"
  echo "then try '${SCRIPTNAME_}' again."
  echo
  exit 1
fi

# ---------------------------
# count_errors()
#
count_errors() {
  egrep -e "\.py\:[0-9]+\:" fixme.lint.txt \
    | wc -l | sed -E 's/[^0-9]*([0-9]+).*/\1/'
}

# ---------------------------
# lint the source
#
pushd src/authenticator > /dev/null
flake8 --exclude=ez_setup.py --max-complexity=10 . > fixme.lint.txt 2>&1
pep257 --match='(?!ez_setup).*\.py' . >> fixme.lint.txt 2>&1
ERROR_COUNT_=`count_errors`
if (( 0 == ERROR_COUNT_ )); then
  echo "$(tput setaf 10)./src/authenticator is OK.$(tput sgr0)"
else
  echo "$(tput setaf 9)./src/authenticator has $ERROR_COUNT_ issues.$(tput sgr0)"
fi
popd > /dev/null

pushd tests > /dev/null
flake8 --max-complexity=10 . > fixme.lint.txt 2>&1
pep257 --match='.*\.py' . >> fixme.lint.txt 2>&1
ERROR_COUNT_=`count_errors`
if (( 0 == ERROR_COUNT_ )); then
  echo "$(tput setaf 10)./tests is OK.$(tput sgr0)"
else
  echo "$(tput setaf 9)./tests has $ERROR_COUNT_ issues.$(tput sgr0)"
fi
popd > /dev/null
