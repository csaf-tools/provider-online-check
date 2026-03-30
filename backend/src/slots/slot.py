# Class representation of a CSAF checker / validator procedure
# Runs in its own thread. Communicates progress & results with
# a dedicated client object.
# Invokes database caching on success

# Involved in: 7, 8, 9, 12

import asyncio
import logging
from typing import Annotated

from pydantic import BaseModel, Field

# from ..router.redis import get_redis
from ..router.scan_request import ScanRequest
from ..router.scan_response import ScanResponseStatus
from .domain_task import Domain_Task, Domain_Task_Status

logger = logging.getLogger(__name__)


class Slot(BaseModel):
    id: Annotated[
        int, Field(description="Slot identifier, mostly for debugging purposes")
    ] = 0

    running_task: Annotated[
        Domain_Task, Field(description="Currently running domain task for this slot")
    ] = None

    @classmethod
    def create(cls, id: int) -> "Slot":
        data = {
            "id": id,
        }
        return cls(**data)

    def start_domain_task(self, request: ScanRequest) -> str:
        # Stop potentially running task
        if self.running_task is not None:
            self.running_task.stop_task()

        # Create and run task in background
        self.running_task = Domain_Task.create(request.domain, request.session_id)
        asyncio.create_task(self.running_task.run_checker())

        return self.running_task.get_data(False).uuid

    # Returns true if no running task exists or running task is either done, interrupted or in an erroneous state
    def is_available(self) -> bool:
        if self.running_task is None:
            return True

        if self.running_task.get_status() == Domain_Task_Status.DONE:
            return True

        if not self.running_task.is_in_valid_state():
            return True

        return False

    # Returns true, if no running task exists or running task is orphaned
    # A task is considered orphaned, if each listener to this task has disconnected for a while
    def is_task_orphaned(self) -> bool:
        if self.running_task is None:
            return True

        if self.running_task.is_orphaned():
            return True

        return False

    # Translates task status to scan response status
    # Adds appropriate error message if necessary
    def getSlotStatusResponse(self) -> (ScanResponseStatus, str):
        if self.running_task is None:
            return ScanResponseStatus.UNDEFINED, "No running task found"
        elif self.running_task.is_paused():
            return ScanResponseStatus.PAUSED, ""
        elif self.running_task.get_status() == Domain_Task_Status.ERROR:
            return ScanResponseStatus.ERROR, "A backend error occured"
        elif self.running_task.get_status() == Domain_Task_Status.INTERRUPTED:
            return ScanResponseStatus.ERROR, "Task has been stopped manually"
        elif self.running_task.get_status() == Domain_Task_Status.DONE:
            return ScanResponseStatus.DONE_CHECKER, ""
        elif len(self.running_task.get_data(False).csaf_checker_output_runtime_log) == 0:
            return ScanResponseStatus.INITIALIZED, ""

        return ScanResponseStatus.RUNNING_CHECKER, ""
