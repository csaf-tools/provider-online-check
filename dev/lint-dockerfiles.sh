#!/bin/bash

# Import utils package
. "$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )/util.sh"

# This uses Hadolint (https://github.com/hadolint/hadolint) to lint all Service Dockerfiles
# Pull Hadolint
docker pull ghcr.io/hadolint/hadolint

lint_all_files() {
    LOCAL_PATH="$1"
    (
        cd "./$LOCAL_PATH" || abort 1
        info "Linting Dockerfile in $LOCAL_PATH"
        docker run --rm -i ghcr.io/hadolint/hadolint < Dockerfile
    )
}

# Lint all directories with Dockerfiles
lint_all_files dev/act
lint_all_files backend
lint_all_files frontend
