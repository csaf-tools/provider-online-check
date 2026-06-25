#!/bin/bash

# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# Import utils package
. "$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )/../util.sh"

# Generates SBOMs in CycloneDX and SPDX formats via syft
# Uses a Docker-in-Docker approach to build and generate SBOMs inside a container environment
# Call this script only from its associated make target

# Parameters
GENERATED_FILE_PATH=${GENERATED_FILE_PATH:-"./sboms/"}

if [ ! -d "$GENERATED_FILE_PATH" ]
then
    error "Generated files destination does not exist"
    error "Path $(realpath $GENERATED_FILE_PATH) not found"
    exit 1
fi

if [[ "${GENERATED_FILE_PATH: -1}" != "/" ]]
then
    GENERATED_FILE_PATH="${GENERATED_FILE_PATH}/"
fi

IMAGE_TAG_SYFT="syft-sboms-image"
CONTAINER_NAME_SYFT="syft-sboms-active-container"

# Read settings from environment variable file
set -a
. "$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )/../../.env"
set +a

IMAGE_TAG_BACKEND="csaf-provider-online-check-backend"
IMAGE_TAG_FRONTEND="csaf-provider-online-check-frontend"

# Build Images
docker build -t "$IMAGE_TAG_SYFT" ./dev/sboms/
docker build -t "$IMAGE_TAG_BACKEND" --build-arg "CSAF_SHA256=${CSAF_SHA256}" --build-arg "CSAF_CHECKER_VERSION=${CSAF_CHECKER_VERSION}" ./backend/
docker build -t "$IMAGE_TAG_FRONTEND" ./frontend/

# Run Syft container
cleanup()
{
    info "Cleanup"
    docker stop "$CONTAINER_NAME_SYFT"
    docker rm "$CONTAINER_NAME_SYFT"
    success "Done"
    exit 0
}

trap 'cleanup' SIGINT EXIT
docker run -d -v /var/run/docker.sock:/var/run/docker.sock -v ./:/app/ --name "$CONTAINER_NAME_SYFT" "$IMAGE_TAG_SYFT"

# Generate SBOMs
info "Generating SBOMs for backend"
docker exec "$CONTAINER_NAME_SYFT" syft "$IMAGE_TAG_BACKEND" -o cyclonedx-json="$GENERATED_FILE_PATH"sbom-backend-cyclonedx.json

info "Generating SBOMs for frontend"
# Use cyclonedx-node-npm against package-lock.json for accurate npm dependency scope
docker exec "$CONTAINER_NAME_SYFT" cyclonedx-npm \
    --package-lock-only \
    --ignore-npm-errors \
    --output-format JSON \
    --output-file "${GENERATED_FILE_PATH}sbom-frontend-cyclonedx.json" \
    /app/frontend/package-lock.json

# Post-process and convert — all run inside the container to avoid permission issues
# (syft writes files as root; running python3 and syft in the same container avoids host permission errors)
APP_VERSION=$(git describe --tags 2>/dev/null || echo "${APP_VERSION:-unknown}")

info "Completing SBOMs (filtering and patching metadata)"
docker exec "$CONTAINER_NAME_SYFT" python3 /app/dev/sboms/complete_sbom.py "${GENERATED_FILE_PATH}sbom-backend-cyclonedx.json"  "csaf-provider-online-check-backend"  "$APP_VERSION"
docker exec "$CONTAINER_NAME_SYFT" python3 /app/dev/sboms/complete_sbom.py "${GENERATED_FILE_PATH}sbom-frontend-cyclonedx.json" "csaf-provider-online-check-frontend" "$APP_VERSION"

# Convert patched CycloneDX files to SPDX
info "Converting CycloneDX to SPDX"
docker exec "$CONTAINER_NAME_SYFT" syft convert "${GENERATED_FILE_PATH}sbom-backend-cyclonedx.json"  -o spdx-json | jq . > "${GENERATED_FILE_PATH}sbom-backend-spdx.json"
docker exec "$CONTAINER_NAME_SYFT" syft convert "${GENERATED_FILE_PATH}sbom-frontend-cyclonedx.json" -o spdx-json | jq . > "${GENERATED_FILE_PATH}sbom-frontend-spdx.json"
