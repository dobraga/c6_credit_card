#!/bin/bash
# This script runs the C6 credit card analysis tool.
# Ensure you have installed the project and its dependencies first, e.g., by running:
# uv pip install -e .[dev]

clear
# Option 1: Run using the script defined in pyproject.toml
uv run c6_credit_card -p "./faturas"

# Option 2: Run as a module (should also work after 'uv pip install -e .')
# uv run python -m c6_credit_card -p "./faturas"

# The arguments "-p ./faturas" are passed to the script.
# If you need to pass different arguments, you can modify them here or pass them when calling run.sh,
# for example: ./run.sh -p "another_folder"
# To do that, the script would need to be: uv run c6_credit_card "$@"
# For now, keeping it simple with the hardcoded argument.
