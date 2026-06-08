#!/bin/bash

# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

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

IMAGE_TAG_BACKEND="csaf-provider-online-check-backend"
IMAGE_TAG_FRONTEND="csaf-provider-online-check-frontend"
IMAGE_TAG_VALIDATOR="csaf-provider-online-check-validator"
IMAGE_TAG_VALKEY="valkey/valkey:8-alpine"

# Build Images
docker build -t "$IMAGE_TAG_SYFT" ./dev/sboms/
docker build -t "$IMAGE_TAG_BACKEND" ./backend/
docker build -t "$IMAGE_TAG_FRONTEND" ./frontend/
docker build -t "$IMAGE_TAG_VALIDATOR" ./validator/

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
docker exec "$CONTAINER_NAME_SYFT" syft "$IMAGE_TAG_BACKEND" -o spdx-json="$GENERATED_FILE_PATH"sbom-backend-spdx.json

info "Generating SBOMs for frontend"
docker exec "$CONTAINER_NAME_SYFT" syft "$IMAGE_TAG_FRONTEND" -o cyclonedx-json="$GENERATED_FILE_PATH"sbom-frontend-cyclonedx.json
docker exec "$CONTAINER_NAME_SYFT" syft "$IMAGE_TAG_FRONTEND" -o spdx-json="$GENERATED_FILE_PATH"sbom-frontend-spdx.json

info "Generating SBOMs for validator"
docker exec "$CONTAINER_NAME_SYFT" syft "$IMAGE_TAG_VALIDATOR" -o cyclonedx-json="$GENERATED_FILE_PATH"sbom-validator-cyclonedx.json
docker exec "$CONTAINER_NAME_SYFT" syft "$IMAGE_TAG_VALIDATOR" -o spdx-json="$GENERATED_FILE_PATH"sbom-validator-spdx.json

info "Generating SBOMs for valkey"
docker exec "$CONTAINER_NAME_SYFT" syft "$IMAGE_TAG_VALKEY" -o cyclonedx-json="$GENERATED_FILE_PATH"sbom-valkey-cyclonedx.json
docker exec "$CONTAINER_NAME_SYFT" syft "$IMAGE_TAG_VALKEY" -o spdx-json="$GENERATED_FILE_PATH"sbom-valkey-spdx.json
