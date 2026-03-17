# Class representation of a CSAF checker / validator procedure
# Runs in its own thread. Communicates progress & results with
# a dedicated client object.
# Invokes database caching on success

# Involved in: 7, 8, 9, 12

import logging
from typing import Annotated
from pydantic import BaseModel, Field

# from ..router.redis import get_redis
from ..router.scan_request import ScanRequest
from .domain_task import Domain_Task, Domain_Task_Status

logger = logging.getLogger(__name__)

class Slot(BaseModel):
    id: Annotated[
        int,
        Field(description="Slot identifier, mostly for debugging purposes")
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
        # FIXME
        # Handle old domain task if it exists
        if self.running_task is not None:
            self.running_task = None

        # Create new domain task
        self.running_task = Domain_Task.create(request.domain, request.session_id)

        # Run Task (in background)
        self.running_task.run_checker()

        return self.running_task.uuid

    def is_available(self) -> bool:
        if self.running_task is None:
            return True

        if self.running_task.status == Domain_Task_Status.DONE:
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
