FROM python:3.11-slim

WORKDIR /app

# for the development, don't cache and optimize anything
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY . .

RUN chmod 777 -R .
RUN pip install --no-cache-dir -r requirements.txt && \
    chmod +x ./dev/run-lint.sh

EXPOSE 8000

# with hot-reloading
CMD ["./command.sh"]
