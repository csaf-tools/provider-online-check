#!/bin/bash

# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

set -e

# Due to docker compose volume mounting, we need to reinstall all pip packages
pip install -r requirements.txt

# Install csaf binary as well
: "${CSAF_CHECKER_VERSION:?CSAF_CHECKER_VERSION is not set}"

if [ -n "${CSAF_REF}" ]; then
    echo "Building csaf_checker from gocsaf source at ref: ${CSAF_REF}"

    rm -rf /tmp/gocsaf  # may exist from a previous container start
    git clone https://github.com/gocsaf/csaf.git /tmp/gocsaf
    git -C /tmp/gocsaf checkout "${CSAF_REF}"
    (
        cd /tmp/gocsaf || exit 1
        make build_linux
        git rev-parse --short HEAD > /app/bin/csaf_revision
    ) || { echo "Error building csaf_checker from source" && exit 1; }
    rm -rf /tmp/gocsaf
else
    (
        mkdir -p bin
        cd bin || exit 1

        # Download from GitHub
        curl -LO "https://github.com/gocsaf/csaf/releases/download/v${CSAF_CHECKER_VERSION}/csaf-${CSAF_CHECKER_VERSION}-gnulinux-amd64.tar.gz"

        tar -xzf "csaf-${CSAF_CHECKER_VERSION}-gnulinux-amd64.tar.gz"

        rm "csaf-${CSAF_CHECKER_VERSION}-gnulinux-amd64.tar.gz"

        rm -rf ./csaf-binary
        mv "./csaf-${CSAF_CHECKER_VERSION}-gnulinux-amd64" "./csaf-binary"

    ) || { echo "Error downloading and extracting csaf binary 'csaf-${CSAF_CHECKER_VERSION}-gnulinux-amd64.tar.gz'" && exit 1; }
fi

# Start uvicorn daemon
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
