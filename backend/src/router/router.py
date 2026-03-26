# Accepts HTTP Requests / provides Routes
# Manages "big picture" structure and flow of a http request

# Calls validators - Early exit possible
# Creates client for continuous frontend communication
# Gives slot_manager command to start threaded csaf check/validator

import asyncio
import logging
import os
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ..csaf.csaf_checker import CSAF_BINARY_PATH, CSAF_CHECKER_BINARY
from ..database.database import Database_Manager
from ..database.redis import Redis_Controller
from ..slots.slot_manager import Slot_Manager
from .scan_request import ScanRequest
from .scan_response import ScanResponse, ScanResponseStatus

router = APIRouter()


logger = logging.getLogger(__name__)


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
        # ----------------- Important thoughts -----------------
        # Starting a scan can have multiple response types:
        #   - Domain already processed by a slotted domain task (Return UUID + Running domain task data)
        #   - Domain not processed, but recently cached (Return Cached domain task data)
        #   - Domain not processed, but no slots available (Return Error)
        #   - Domain not processed and slot avaialable. (Return UUID + Running domain task data)
        #
        # Either start_scan should display data or redirect to get_data (in case no error has been returned)
        # ------------------------------------------------------
        uuid = Slot_Manager().start_domain_task(request)

        if uuid == "":
            # No slot is available
            return {
                "status": ScanResponseStatus.ERROR,
                "domain": request.domain,
                "error": "Server is over capacity, try again later",
            }

        return {
            "status": ScanResponseStatus.INITIALIZED,
            "domain": request.domain,
            "task_id": uuid,
            "runtime_output": [f"Visit 48090/api/scan/get/{str(uuid)} to see results"],
            "results_checker": str(uuid),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scan: {str(e)}")


@router.get(
    "/scan/get/{task_id}",
    summary="Get output of scan",
    description="Get latest feedback of scan, either from cache or from running task",
    tags=["scan"],
    status_code=status.HTTP_200_OK,
)
async def get_scan(task_id: str) -> Dict[str, Any]:
    """
    Returns the current or cached output of the domain task which is running or has run
    csaf checker on the associated domain
    """

    # 1. Find domain task in running task
    slot = Slot_Manager().get_slot_by_task_id(task_id)

    if slot is not None:
        data = slot.running_task.get_data()
    else:
        # 2. Find domain task in database cache
        data = Database_Manager().load_task_by_id(task_id)

    if data is None:
        return {"status": ScanResponseStatus.ERROR}

    try:
        return {
            "status": ScanResponseStatus.RUNNING_CHECKER,
            "runtime_output": data.csaf_checker_output_runtime_log,
            "results_checker": data.csaf_checker_output_result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scan: {str(e)}")


@router.get("/health", summary="Health Check", tags=["devops"])
async def health_check():
    """Check for free slots and csaf_checker binary"""
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
        redis_available = Redis_Controller()._redis.ping()
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
