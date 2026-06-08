#!/bin/bash

# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

# Executes all linters

echo "Run Linters"

# Parameters
while getopts "lib" FLAG; do
    case "${FLAG}" in
    l) LOCAL=true;;
    i) INSTALL=true;;
    b) NOT_IN_BACKEND=true;;
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
    make dev-detached

    # Container Mode
    eval "$DC exec backend black ${PATHS}"
    eval "$DC exec backend isort ${PATHS}"
    eval "$DC exec backend flake8 --ignore=E501 ${PATHS}"

else
    # Local Mode
    echo "Black"
    black ${PATHS}
    echo "Isort"
    isort ${PATHS}
    echo "Flake8"
    flake8 --ignore=E501 ${PATHS}
fi
