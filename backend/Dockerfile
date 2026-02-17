# --- Shared base ---
FROM ubuntu:22.04 AS base

# Install Python and curl
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3=3.10.6-1~22.04.1 \
    python3-pip=22.0.2+dfsg-1ubuntu0.7 \
    curl=7.81.0-1ubuntu1.21 && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Dev target ---
FROM base AS dev

# for development, don't cache and optimize anything
ENV PYTHONDONTWRITEBYTECODE=1

COPY . .

RUN chmod 777 -R . && chmod -x ./command.sh && \
    chmod +x ./dev/run-lint.sh

EXPOSE 8000

# with hot-reloading
CMD ["sh", "/app/command.sh"]

# --- Prod target ---
FROM base AS prod

# Download csaf_checker binary
ARG CSAF_VERSION=3.4.0
ARG CSAF_SHA256=d604d17805bb1dfd4fa3c1887c7d109356eb5e36079a3877e37ef9fb412b66b7
WORKDIR /app/bin
RUN curl -LO "https://github.com/gocsaf/csaf/releases/download/v${CSAF_VERSION}/csaf-${CSAF_VERSION}-gnulinux-amd64.tar.gz" && \
    echo "${CSAF_SHA256}  csaf-${CSAF_VERSION}-gnulinux-amd64.tar.gz" | sha256sum -c - && \
    tar -xzf "csaf-${CSAF_VERSION}-gnulinux-amd64.tar.gz" && \
    rm "csaf-${CSAF_VERSION}-gnulinux-amd64.tar.gz" && \
    mv "csaf-${CSAF_VERSION}-gnulinux-amd64" csaf-binary
WORKDIR /app

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
