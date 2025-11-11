# Accepts HTTP Requests / provides Routes
# Manages "big picture" structure and flow of a http request

# Calls validators - Early exit possible
# Creates client for continuous frontend communication
# Gives slot_manager command to start threaded csaf check/validator

# Involved in: 3, basically everything else too

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, validator
from typing import Dict, Any

from ..validators.request_validator import validate_domain
from ..client.client import ScanResponse

router = APIRouter()

class ScanRequest(BaseModel):
    domain: str = Field(
        ...,
        description="Domain to scan for CSAF provider metadata",
        example="example.com"
    )

    @validator("domain", pre=True)
    def _validate_domain(cls, v):
        # delegate validation to the external validator
        return validate_domain(v)


@router.get("/", summary="API root", tags=["main"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "CSAF Provider Scan API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@router.post(
    "/scan/start",
    response_model=ScanResponse,
    summary="Start a domain scan",
    description="Initiates a scan for CSAF provider metadata on the specified domain",
    tags=["scan"],
    status_code=status.HTTP_201_CREATED
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
        # FIXME: Add real scan logic here
        return {
            "status": "started",
            "domain": request.domain,
            "message": f"Scan initiated for domain: {request.domain}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scan: {str(e)}")


@router.get("/health", summary="Health Check", tags=["devops"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


