from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import re
from typing import Dict, Any

app = FastAPI(
    title="CSAF Provider Scan API",
    description="API for scanning CSAF providers",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)


class ScanRequest(BaseModel):
    domain: str = Field(
        ...,
        description="Domain to scan for CSAF provider metadata",
        example="example.com"
    )

    @validator('domain')
    def validate_domain(cls, v):
        """Validate domain format"""
        if not v or not v.strip():
            raise ValueError("Domain cannot be empty")

        # Basic domain validation
        # FIXME: Use validators.domain?
        domain_pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
        if not re.match(domain_pattern, v.strip()):
            raise ValueError("Invalid domain format")

        return v.strip()


class ScanResponse(BaseModel):
    # Dummy structure
    status: str = Field(..., description="Status of the scan request")
    domain: str = Field(..., description="Domain being scanned")
    message: str = Field(..., description="Additional information about the scan")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "CSAF Provider Scan API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.post(
    "/scan/start",
    response_model=ScanResponse,
    summary="Start a domain scan",
    description="Initiates a scan for CSAF provider metadata on the specified domain",
    tags=["scan"]
)
async def start_scan(request: ScanRequest) -> Dict[str, Any]:
    """
    Start a scan for the provided domain.

    Args:
        request: ScanRequest containing the domain to scan

    Returns:
        ScanResponse with scan status and details

    Raises:
        HTTPException: If the scan cannot be initiated
    """
    try:
        # FIXME: Add logic
        return {
            "status": "started",
            "domain": request.domain,
            "message": f"Scan initiated for domain: {request.domain}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scan: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
