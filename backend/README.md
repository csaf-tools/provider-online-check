# CSAF Provider Scan Backend

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
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

## API Endpoints

### POST /api/scan/start
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

### GET /api/health
Health check endpoint.

### GET /api/
Root endpoint with API information.
