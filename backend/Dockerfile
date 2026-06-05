# --- Shared base ---
FROM ubuntu:22.04 AS base

ARG CSAF_CHECKER_VERSION
ENV CSAF_CHECKER_VERSION=${CSAF_CHECKER_VERSION}

# Install Python and curl
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    curl && \
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

# Download swagger-ui-bundle.js and swagger-ui.css, using the version FastAPI expects
RUN SWAGGER_UI_VERSION=$(python3 -c "import re; from fastapi.openapi.docs import get_swagger_ui_html; print(re.search(r'swagger-ui-dist@([\w.]+)', get_swagger_ui_html(openapi_url='/api/openapi.json', title='title').body.decode()).group(1))") && \
    mkdir -p /app/static/swagger-ui && \
    curl -Lf "https://cdn.jsdelivr.net/npm/swagger-ui-dist@${SWAGGER_UI_VERSION}/swagger-ui-bundle.js" -o /app/static/swagger-ui/swagger-ui-bundle.js && \
    curl -Lf "https://cdn.jsdelivr.net/npm/swagger-ui-dist@${SWAGGER_UI_VERSION}/swagger-ui.css" -o /app/static/swagger-ui/swagger-ui.css

# Download csaf_checker binary
ARG CSAF_SHA256
WORKDIR /app/bin
RUN curl -LO "https://github.com/gocsaf/csaf/releases/download/v${CSAF_CHECKER_VERSION}/csaf-${CSAF_CHECKER_VERSION}-gnulinux-amd64.tar.gz" && \
    echo "${CSAF_SHA256}  csaf-${CSAF_CHECKER_VERSION}-gnulinux-amd64.tar.gz" | sha256sum -c - && \
    tar -xzf "csaf-${CSAF_CHECKER_VERSION}-gnulinux-amd64.tar.gz" && \
    rm "csaf-${CSAF_CHECKER_VERSION}-gnulinux-amd64.tar.gz" && \
    mv "csaf-${CSAF_CHECKER_VERSION}-gnulinux-amd64" csaf-binary
WORKDIR /app

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
