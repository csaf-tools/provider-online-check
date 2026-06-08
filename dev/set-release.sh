#!/bin/bash

# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

# Set the APP_VERSION in .env to the currently correct semantic version according to git
# Source:
# https://github.com/gocsaf/csaf/blob/586524a97e42c3fa5b97fbcb4e1169ad1df064da/Makefile#L50-L60

# don't use --dirty=-modified here as there will always be local changes to .env for configuration
gitdesc=$(git describe --tags --always )
# extract the patch number from gitdesc
gitdescpatch=$(echo "$gitdesc" | sed -E 's/v?[0-9]+\.[0-9]+\.([0-9]+)[-+]?.*/\1/')
# increase the patch number by one, as in semver a `-` postfix means pre-release and there is no specifier for post-releases
semverpatch=$(( gitdescpatch + 1 ))
# The second regexp in the next line only matches
# if there is a hyphen (`-`) followed by a number,
# by which we assume that git describe has added a string after the tag
# If there is no commit-specifier in gitdesc, then the patch number stays unchanged
semver=$(echo "$gitdesc" | sed -E -e "s/([0-9]+\.[0-9]+\.)([0-9]+)(-[1-9].*)/\1${semverpatch}\3/")

echo "Set version to ${semver}."
sed -Ei "s/^APP_VERSION=.*?/APP_VERSION=$semver/" "$(readlink -f "$(dirname "$0")")/../.env"
