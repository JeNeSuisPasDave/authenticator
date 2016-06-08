#! /bin/bash
#
# This script assumes that Python 3.5 is installed via Mac Ports.
# If Python 3.5 is installed some other way, then the script will
# need some adjustment.
#

SCRIPTNAME_="$0"

# Get the directory holding this script
# (method from: http://stackoverflow.com/a/12694189/1392864)
#
SCRIPTDIR_="${BASH_SOURCE%/*}"
if [[ ! -d "$DIR" ]]; then DIR="$PWD"; fi

# Python install info
#
VENV_DIRNAME_=venv35
SAVE_VENV_DIRNAME_=""
PYTHON_VERSION_=3.5
PYTHON_INSTALLROOT_=/opt/local/Library/Frameworks/Python.framework/Versions
PYTHON_INSTALLBASE_=${PYTHON_INSTALLROOT_}/${PYTHON_VERSION_}

# Check whether Python 3.5 is installed via Mac Ports
#
if ! [ -d "${PYTHON_INSTALLBASE_}" ]; then
  echo "ERROR: Python 3.5 is not installed."
  echo "       Expected '${PYTHON_INSTALLBASE_}'"
  echo "Install using 'sudo port install python35'."
  exit 2
fi

# Check whether we are running in a python virtual environment
#
export VENV_RUNNING=`env | grep VIRTUAL_ENV | wc -l | tr -d [[:space:]]`
#echo "VENV_RUNNING: ${VENV_RUNNING}"
if [ 0 != ${VENV_RUNNING} ]; then
  echo "ERROR: Python virtual environment already running"
  echo
  echo "Try 'deactivate' to stop the virtual environment, and"
  echo "then try '${SCRIPTDIR_}/make-venv35.sh' again."
  echo
  exit 4
fi

# Check whether the virtual environment directory already exists
#
if [ -e "./${VENV_DIRNAME_}" ]; then
  echo "WARNING: virtual environment directory ./${VENV_DIRNAME_} already exists."
  read -p "Do you want to delete and replace it? [y/N]" -n 1 -r
  echo    # (optional) move to a new line
  if [[ ! $REPLY =~ ^[Yy]$ ]]
  then
    echo "No action taken".
    exit 6
  fi
  # Rename the existing directory
  #
  SAVE_VENV_DIRNAME_="${VENV_DIRNAME_}_bkup"
  mv "./${VENV_DIRNAME_}" "./$SAVE_VENV_DIRNAME_"
fi

# Create the virtual environment directory (the deployment folder)
#
"${PYTHON_INSTALLBASE_}/bin/python3" -m venv "${VENV_DIRNAME_}"
if [ -d "./${VENV_DIRNAME_}" ]; then
  if ! [ -z "${SAVE_VENV_DIRNAME_}" ]; then
    rm -rf "./${SAVE_VENV_DIRNAME_}"
  fi
else
  echo "ERROR: virtual environment not created."
  if ! [ -z "${SAVE_VENV_DIRNAME_}" ]; then
    mv "./${SAVE_VENV_DIRNAME_}" "./${VENV_DIRNAME_}"
  fi
  exit 8
fi

# Activate the virtual environment
#
. "${VENV_DIRNAME_}/bin/activate"
# Check whether we are running in a python virtual environment
#
export VENV_RUNNING=`env | grep VIRTUAL_ENV | wc -l | tr -d [[:space:]]`
#echo "VENV_RUNNING: ${VENV_RUNNING}"
if [ 0 == ${VENV_RUNNING} ]; then
  echo "ERROR: Python virtual environment was not activated; not running"
  exit 10
fi

# Check whether we are running Python 3.5
#
export PYVER_=`python --version 2>&1 | grep "^Python 3\.5\." | wc -l | tr -d [[:space:]]`
if [ 0 == ${PYVER_} ]; then
  echo "ERROR: Python 3.5 is required. Found "`python --version`"."
  echo
  deactivate
  exit 12
fi

# Update setuptools and pip
#
pip install --upgrade -q setuptools
pip install --upgrade -q pip

# deactivate the virtual environment
#
deactivate

# Done!
#
echo ""
echo "OK. Virtual environment for Python 3.5 is created."
echo "Use source command '. ${SCRIPTDIR_}/activate-project.src' to start;"
echo "Use command alias 'deactivate-project' to stop."
echo ""
