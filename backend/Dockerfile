FROM ubuntu:22.04

WORKDIR /app

# Install python
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip curl && \
    rm -rf /var/lib/apt/lists/*

# for development, don't cache and optimize anything
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY . .

RUN chmod 777 -R . && chmod -x ./command.sh
RUN pip install --no-cache-dir -r requirements.txt && \
    chmod +x ./dev/run-lint.sh

EXPOSE 8000

# with hot-reloading
CMD ["sh", "/app/command.sh"]
