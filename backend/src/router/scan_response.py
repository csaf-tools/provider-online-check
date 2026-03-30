from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field


class ScanResponseStatus(Enum):
    UNDEFINED = "UNDEFINED"  # No status has been set for some reason or another. Default value and likely caused by an error
    INITIALIZED = "INITIALIZED"  # Slot has been assigned successfully, but domain task hasn't started yet
    ERROR = "ERROR"  # Domain task couldn't be started or ended early because of some error (see error field)
    RUNNING_CHECKER = "RUNNING_CHECKER"  # Domain task is running CSAF Checker
    DONE_CHECKER = "DONE_CHECKER"  # CSAF Checker is done
    CACHED_CHECKER = "CACHED_CHECKER"  # CSAF Checker output has been found for requested domain in database cache. No domain task has been started
    PAUSED = "PAUSED"  # Domain task is paused


class ScanResponse(BaseModel):
    domain: Annotated[
        str,
        Field(description="Status of the scan request"),
    ]

    status: Annotated[
        ScanResponseStatus,
        Field(description="Status of the scan request"),
    ] = ScanResponseStatus.UNDEFINED
    slot_id: Annotated[
        int, Field(description="Slot id the domain task is performed in")
    ] = -1
    error: Annotated[str, Field(description="Latest error message")] = ""

    runtime_output: Annotated[
        list[str],
        str,
        Field(description="Runtime output provided by CSAF Checker in verbose mode"),
    ] = []
    results_checker: Annotated[
        str,
        Field(description="Results of CSAF Checker"),
    ] = []
