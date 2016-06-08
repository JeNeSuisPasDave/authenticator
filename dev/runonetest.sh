#! /bin/bash
#
PYTHONPATH="$(pwd)/src" python -m unittest \
	tests.test_CLI.CoreCLITests.test_list_with_three_configs_verbose
