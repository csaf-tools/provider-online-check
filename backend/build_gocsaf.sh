#!/bin/bash

# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

echo "Building csaf_checker from gocsaf source at ref: ${CSAF_REF}"

git clone https://github.com/gocsaf/csaf.git /tmp/gocsaf
git -C /tmp/gocsaf checkout "${CSAF_REF}"
cd /tmp/gocsaf
make build_linux
mkdir -p /app/bin/csaf-binary
cp -r bin-linux-amd64 /app/bin/csaf-binary/
git rev-parse --short HEAD > /app/bin/csaf_revision
rm -rf /tmp/gocsaf
