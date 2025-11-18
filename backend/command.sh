#!/bin/bash
set -e

# Due to docker compose volume mounting, we need to reinstall all pip packages
pip install -r requirements.txt

# Install csaf binary as well
CSAF_VERSION="3.4.0"
(
    mkdir .csaf || true
    cd .csaf || exit 1

    # Download from GitHub
    curl -LO "https://github.com/gocsaf/csaf/releases/download/v${CSAF_VERSION}/csaf-${CSAF_VERSION}-gnulinux-amd64.tar.gz"

    tar -xzf "csaf-${CSAF_VERSION}-gnulinux-amd64.tar.gz"

    rm "csaf-${CSAF_VERSION}-gnulinux-amd64.tar.gz"

    rm -rf ./csaf-binary
    mv "./csaf-${CSAF_VERSION}-gnulinux-amd64" "./csaf-binary"

) || { echo "Error downloading and extracting csaf binary 'csaf-${CSAF_VERSION}-gnulinux-amd64.tar.gz'" && exit 1; }

# Start uvicorn daemon
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

