#! /bin/bash
#
PYTHONPATH=$(pwd)/src pyi-makespec \
  --specpath src/exe-spec \
  -n authenticator \
  --log-level=WARN \
  -D -c \
  src/authenticator/cli.py
