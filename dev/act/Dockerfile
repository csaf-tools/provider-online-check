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

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN curl --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/nektos/act/master/install.sh | bash

# Copy repository content
COPY . .

CMD [ "sleep" , "infinity" ]
