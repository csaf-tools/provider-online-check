# --- Shared base ---
FROM ubuntu:22.04 AS base

# Install Python and curl
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip curl && \
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
RUN mkdir -p bin && cd bin && \
    curl -LO "https://github.com/gocsaf/csaf/releases/download/v${CSAF_VERSION}/csaf-${CSAF_VERSION}-gnulinux-amd64.tar.gz" && \
    tar -xzf "csaf-${CSAF_VERSION}-gnulinux-amd64.tar.gz" && \
    rm "csaf-${CSAF_VERSION}-gnulinux-amd64.tar.gz" && \
    mv "csaf-${CSAF_VERSION}-gnulinux-amd64" csaf-binary

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
