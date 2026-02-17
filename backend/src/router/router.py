# Accepts HTTP Requests / provides Routes
# Manages "big picture" structure and flow of a http request

# Calls validators - Early exit possible
# Creates client for continuous frontend communication
# Gives slot_manager command to start threaded csaf check/validator

# Involved in: 3, basically everything else too

import asyncio
import os
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ..csaf.csaf_checker import CSAF_BINARY_PATH, CSAF_CHECKER_BINARY
from ..slots.slot_manager import Slot_Manager
from .redis import Redis
from .scan_request import ScanRequest
from .scan_response import ScanResponse, ScanResponseStatus

router = APIRouter()


@router.get("/", summary="API root", tags=["main"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "CSAF Provider Scan API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "openapi": "/api/openapi.json",
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
        slot = await Slot_Manager().start_domain_task(request)

        if slot is None:
            # No slot is available
            return {
                "status": ScanResponseStatus.ERROR,
                "domain": request.domain,
                "error": "Server is over capacity, try again later",
            }

        json_result = slot.running_task.data.results_to_json()

        return {
            "status": ScanResponseStatus.INITIALIZED,
            "domain": request.domain,
            "runtime_output": slot.running_task.data.csaf_checker_output_runtime_log,
            "results_checker": json_result,
            "slot_id": slot.id,
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
            "status": ScanResponseStatus.ERROR,
            "domain": request.domain,
            "error": "Path not implemented yet",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scan: {str(e)}")


@router.get("/health", summary="Health Check", tags=["devops"])
async def health_check():
    """Check fir free slots and csaf_checker binary"""
    errors = []

    # Check free slots
    slot_manager = Slot_Manager()
    free_slots = sum(1 for slot in slot_manager.slots if slot.is_available())

    # Check csaf_checker binary
    checker_path = os.path.join(CSAF_BINARY_PATH, CSAF_CHECKER_BINARY)
    binary_available = False
    try:
        # Should probably improved (cached?)
        proc = await asyncio.create_subprocess_exec(
            os.path.abspath(checker_path),
            "--help",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        returncode = await proc.wait()
        binary_available = returncode == 0
    except Exception:
        binary_available = False

    if not binary_available:
        errors.append("csaf_checker binary is not available")

    # Check Redis connectivity
    redis_available = False
    try:
        redis_available = Redis()._redis.ping()
    except Exception:
        redis_available = False
    if not redis_available:
        errors.append("Redis is not available")

    healthy = len(errors) == 0
    response = {
        "status": "healthy" if healthy else "unhealthy",
        "free_slots": free_slots,
        "total_slots": len(slot_manager.slots),
        "csaf_checker_available": binary_available,
        "redis_available": redis_available,
    }

    if errors:
        response["errors"] = errors
        return JSONResponse(content=response, status_code=503)

    return response
