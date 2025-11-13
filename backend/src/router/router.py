# Accepts HTTP Requests / provides Routes
# Manages "big picture" structure and flow of a http request

# Calls validators - Early exit possible
# Creates client for continuous frontend communication
# Gives slot_manager command to start threaded csaf check/validator

# Involved in: 3, basically everything else too

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, validator

from ..client.client import ScanResponse

from ..validators.client_validator import validate_client_blocklist_check
from ..validators.request_validator import validate_domain

router = APIRouter()

class ScanRequest(BaseModel):
    session_id: str = Field(
        description="Unique session id"
    )
    domain: str = Field(
        ...,
        description="Domain to scan for CSAF provider metadata",
        example="example.com",
    )

    @validator("domain", pre=True)
    def _validate_domain(cls, v):
        # delegate validation to the external validator
        return validate_domain(v)
    

    @validator("session_id", pre=True)
    def _validate_client_blocklist_check(cls, v):
        # delegate validation to the external validator
        return validate_client_blocklist_check(v)


@router.get("/", summary="API root", tags=["main"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "CSAF Provider Scan API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@router.post(
    "/scan/start",
    response_model=ScanResponse,
    summary="Start a domain scan",
    description="Initiates a scan for CSAF provider metadata on the specified domain",
    tags=["scan"],
    status_code=status.HTTP_201_CREATED,
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

@router.get(
    "/scan/get/{slot_id}",
    summary="Get output of scan",
    description="Get latest feedback of scan, either from cache or from stream",
    tags=["scan"],
    status_code=status.HTTP_200_OK,
)
async def get_scan(slot_id: str, request: ScanRequest) -> Dict[str, Any]:
    try:
        # FIXME: Add real scan logic here
        return {
            "status": f"get {slot_id}",
            "domain": request.domain,
            "message": f"Scan initiated for domain: {request.domain}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scan: {str(e)}")


@router.get("/health", summary="Health Check", tags=["devops"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
