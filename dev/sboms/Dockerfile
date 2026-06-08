# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

FROM ubuntu:22.04

# Setup
WORKDIR /app/

# Installs
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    ca-certificates \
    curl \
    docker \
    git \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSfL https://get.anchore.io/syft | sh -s -v -- -b /usr/local/bin

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Copy repository content
COPY . .

CMD [ "sleep" , "infinity" ]
