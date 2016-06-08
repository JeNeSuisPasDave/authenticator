#! /bin/bash
#

# Run this from the root directory of the project
#
PYTHONPATH="$(pwd)/src" python -m unittest discover -s ./tests
