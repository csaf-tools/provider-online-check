# Accepts HTTP Requests / provides Routes
# Manages "big picture" structure and flow of a http request

# Calls validators - Early exit possible
# Creates client for continuous frontend communication
# Gives slot_manager command to start threaded csaf check/validator

import asyncio
import logging
import os

import httpx
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ..csaf.csaf_checker import CSAF_BINARY_PATH, CSAF_CHECKER_BINARY
from ..database.database import Database_Manager
from ..database.valkey import Valkey_Controller
from ..slots.slot_manager import Slot_Manager
from .health_response import HealthResponse
from .information_response import InformationResponse
from .scan_request import ScanRequest
from .scan_response import ScanResponse, ScanResponseStatus

router = APIRouter()


logger = logging.getLogger(__name__)

ENV_CSAF_CHECKER_VERSION = "CSAF_CHECKER_VERSION"
ENV_CSAF_VALIDATOR_VERSION = "CSAF_VALIDATOR_VERSION"
ENV_CSAF_PROVIDER_VERSION = "APP_VERSION"


@router.post(
    "/scan/start",
    response_model=ScanResponse,
    summary="Start a domain scan",
    description="Initiates a scan for CSAF provider metadata on the specified domain",
    tags=["scan"],
    status_code=status.HTTP_201_CREATED,
)
async def start_scan(request: ScanRequest) -> ScanResponse:
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
        #   - Domain not processed and slot available. (Return UUID + Running domain task data)
        #
        # Either start_scan should display data or redirect to get_data (in case no error has been returned)
        # ------------------------------------------------------
        uuid = Slot_Manager().start_domain_task(request)
        status = ScanResponseStatus.ERROR
        errorMsg = ""

        if uuid == "":
            # No slot is available
            return {
                "status": ScanResponseStatus.ERROR,
                "domain": request.domain,
                "error": "Server is over capacity, try again later",
            }

        # 1. Find domain task in running task
        slot = Slot_Manager().get_slot_by_task_id(str(uuid))

        if slot is not None:
            data = slot.running_task.get_data(False)

            status, errorMsg = slot.getSlotStatusResponse()
        else:
            # 2. Find domain task in database cache
            data = Database_Manager().load_task_by_id(uuid)

            if data is not None:
                status = ScanResponseStatus.CACHED_CHECKER

        if data is None or errorMsg != "":
            return {
                "status": ScanResponseStatus.ERROR,
                "domain": request.domain,
                "error": errorMsg,
                "runtime_output": (
                    data.csaf_checker_output_runtime_log if data is not None else []
                ),
            }

        # Shorten output
        full_output = data.csaf_checker_output_runtime_log
        displayed_output = full_output

        if request.prioritize_newest_lines:
            # Latest max_lines entries. Lower boundary clamped at start_at_line
            lower_boundary = max(0, len(full_output) - request.max_lines)
            if request.start_at_line > lower_boundary:
                lower_boundary = request.start_at_line

            displayed_output = full_output[lower_boundary:]  # Slicing is boundary safe
        else:
            # max_lines entries starting from start_at_line
            # fmt: off
            displayed_output = full_output[request.start_at_line:(request.start_at_line + request.max_lines)]  # Slicing is boundary safe

        return {
            "status": status,
            "domain": request.domain,
            "task_id": uuid,
            "runtime_output": displayed_output,
            "results_checker": data.csaf_checker_output_result,
            "files_checked": data.files_checked,
            "latest_file_checked": data.latest_file_checked,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scan: {str(e)}")


@router.get(
    "/information",
    summary="General Provider Information",
    tags=["meta"],
    response_model=InformationResponse,
)
async def meta_info() -> InformationResponse:
    """
    Returns information about the provider and its components, such as version numbers

    Returns:
        InformationResponse with provider information
    """

    csaf_checker_version = os.getenv(ENV_CSAF_CHECKER_VERSION, "")
    csaf_validator_version = os.getenv(ENV_CSAF_VALIDATOR_VERSION, "")
    csaf_provider_version = os.getenv(ENV_CSAF_PROVIDER_VERSION, "")

    return {
        "csaf_checker_version": csaf_checker_version,
        "csaf_validator_version": csaf_validator_version,
        "csaf_provider_version": csaf_provider_version,
        "docs": "/api/docs",
        "openapi": "/api/openapi.json",
    }


@router.get(
    "/health", summary="Health Check", tags=["devops"], response_model=HealthResponse
)
async def health_check() -> HealthResponse:
    """
    Check for free slots and csaf_checker binary
    """
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

    # Check Valkey connectivity
    valkey_available = False
    try:
        valkey_available = Valkey_Controller()._valkey.ping()
    except Exception:
        valkey_available = False
    if not valkey_available:
        errors.append("Valkey is not available")

    # Check Validator connectivity
    validator_available = False
    try:
        async with httpx.AsyncClient() as client:
            validator_response = await client.get(
                "http://validator:8082/api/v1/tests", timeout=10
            )

        # 200 is the expected result
        if validator_response.status_code != 200:
            errors.append(
                f"Validator is not available. Status Code: {validator_response.status_code}"
            )
        else:
            validator_available = True
    except httpx.TimeoutException as e:
        errors.append(f"Validator timed out: {e}")
    except httpx.RequestError as e:
        errors.append(f"Validator is not available: {e}")
    if not validator_available:
        errors.append("Validator is not available")

    healthy = len(errors) == 0
    response = {
        "status": "healthy" if healthy else "unhealthy",
        "free_slots": free_slots,
        "total_slots": len(slot_manager.slots),
        "csaf_checker_available": binary_available,
        "valkey_available": valkey_available,
        "validator_available": validator_available,
    }

    if errors:
        response["errors"] = errors
        return JSONResponse(content=response, status_code=503)

    return response
