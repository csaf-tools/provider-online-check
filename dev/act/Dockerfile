FROM ubuntu:22.04

# Setup
WORKDIR /app/

# Installs
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    ca-certificates=20240203~22.04.1 \
    curl=7.81.0-1ubuntu1.21 \
    docker=1.5-2 \
    git=1:2.34.1-1ubuntu1.15 \
    unzip=6.0-26ubuntu3.2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN curl --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/nektos/act/master/install.sh | bash

# Copy repository content
COPY . .

CMD [ "sleep" , "infinity" ]
