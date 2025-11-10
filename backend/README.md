# CSAF Provider Scanner Backend

FastAPI-based backend

## Setup

If not using Docker:

Optionally: Create a venv.

```bash
pip install -r requirements.txt
```

## Running the Server

### Development
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
python main.py
```

## API Documentation

Once the server is running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## API Endpoints

### POST /scan/start
Start a scan for a domain.

**Request Body:**
```json
{
  "domain": "example.com"
}
```

**Response:**
```json
{
  "status": "started",
  "domain": "example.com",
  "message": "Scan initiated for domain: example.com"
}
```

### GET /health
Health check endpoint.

### GET /
Root endpoint with API information.
