#!/bin/bash

. "$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )/util.sh"

# Executes all linters. Should errors occur, CATCH will be set to 1, causing an erroneous exit code.

shout "Run Linters"

# Parameters
while getopts "lscp" FLAG; do
    case "${FLAG}" in
    l) LOCAL=true ;;
    *) echo "Can't parse flag ${FLAG}" && break ;;
    esac
done

# Setup

DC="docker compose -f docker-compose.yml"
PATHS="./src/"

# Safe Exit
trap 'if [ -z "$LOCAL" ]; then make dev-stop; fi' EXIT

# Execution
if [ -z "$LOCAL" ]
then
    info "Building and running dev container"

    # Setup
    echocmd make dev-attached

    info "Linting"
    # Container Mode
    echocmd eval "$DC exec -T backend black --check --diff ${PATHS}"
    echocmd eval "$DC exec -T backend isort --check-only --diff ${PATHS}"
    echocmd eval "$DC exec -T backend flake8 ${PATHS}"
    echocmd eval "$DC exec -T backend mypy ${PATHS}"

else
    # Local Mode
    echocmd black ${PATHS}
    echocmd isort ${PATHS}
    echocmd flake8 ${PATHS}
    echocmd mypy ${PATHS}
fi
