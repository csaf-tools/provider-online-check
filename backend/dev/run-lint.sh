#!/bin/bash

# Executes all linters. Should errors occur, CATCH will be set to 1, causing an erroneous exit code.

echo "Run Linters"

# Parameters
while getopts "lib" FLAG; do
    case "${FLAG}" in
    l) LOCAL=true && shift 1;;
    i) INSTALL=true && shift 1;;
    b) NOT_IN_BACKEND=true && shift 1;;
    *) echo "Can't parse flag ${FLAG}" && break ;;
    esac
done

if [ -n "$INSTALL" ]
then
    pip install --no-cache-dir -r requirements.txt || true
fi

if [ -n "$NOT_IN_BACKEND" ]
then
    PREPATH="/backend"
fi

# Setup

DC="docker compose -f docker-compose.yml"
PATHS=".$PREPATH/src/"

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

else
    # Local Mode
    echo "Black"
    black ${PATHS}
    echo "Isort"
    isort ${PATHS}
    echo "Flake8"
    flake8 ${PATHS}
fi
