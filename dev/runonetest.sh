#! /bin/bash
#
PYTHONPATH="$(pwd)/src" python -m unittest \
	tests.test_ClientData.CoreClientDataTests.test_string
