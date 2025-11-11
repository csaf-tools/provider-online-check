#!/bin/bash

# Executes all linters. Should errors occur, CATCH will be set to 1, causing an erroneous exit code.

echo "Run Linters"

# Parameters
while getopts "lscp" FLAG; do
    case "${FLAG}" in
    l) LOCAL=true ;;
    *) echo "Can't parse flag ${FLAG}" && break ;;
    esac
done

shift 1
PREPATH=$1

# Setup

DC="docker compose -f docker-compose.yml"
PATHS=".$PREPATH/src/"

echo $LOCAL
# Execution
if [ -z "$LOCAL" ]
then
    echo "Building and running dev container"

    # Safe Exit
    trap 'if [ -z "$LOCAL" ]; then make dev-stop; fi' EXIT

    # Setup
    make dev-attached

    "Linting"
    # Container Mode
    eval "$DC exec -T backend black --check --diff ${PATHS}"
    eval "$DC exec -T backend isort --check-only --diff ${PATHS}"
    eval "$DC exec -T backend flake8 ${PATHS}"
    eval "$DC exec -T backend mypy ${PATHS}"

else
    # Local Mode
    echo "Black"
    black ${PATHS}
    echo "Isort"
    isort ${PATHS}
    echo "Flake8"
    flake8 ${PATHS}
    echo "Mypy"
    mypy ${PATHS}
fi
