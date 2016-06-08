#! /bin/bash
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
  echo "Try '. venv34/bin/activate' to start the virtual environment, and"
  echo "then try '${SCRIPTNAME_}' again."
  echo
  exit 1
fi

# Check whether we are running Python 3
#
export PYVER_=`python --version | grep "^Python 3\." | wc -l | tr -d [[:space:]]`
if [ 0 == ${PYVER_} ]; then
  echo "ERROR: Python 3 is required. Found "`python --version`"."
  echo
  echo "Deactivate the current virtual environment."
  echo "Try '. venv34/bin/activate' to start the virtual environment, and"
  echo "then try '${SCRIPTNAME_}' again."
  echo
  exit 1
fi

PYTHONPATH=$(pwd)/src python -m authenticator.cli $*
