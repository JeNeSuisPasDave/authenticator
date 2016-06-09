#! /bin/bash
#
git clone https://github.com/JeNeSuisPasDave/authenticator
cd authenticator
python3.5 -m venv --clear --copies venv35
. venv35/bin/activate
pip install --quiet --upgrade pip
pip install --quiet --upgrade setuptools
./dev/venv/provision-venv.sh
deactivate
