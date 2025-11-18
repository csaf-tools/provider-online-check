# Class representation of a CSAF checker / validator procedure
# Runs in its own thread. Communicates progress & results with
# a dedicated client object.
# Invokes database caching on success

# Involved in: 7, 8, 9, 12

from typing import Annotated
from pydantic import BaseModel, Field

# from ..router.redis import get_redis
from ..router.scan_request import ScanRequest
from .domain_task import Domain_Task, Domain_Task_Status


class Slot(BaseModel):
    running_task: Annotated[
        Domain_Task, Field(description="Currently running domain task for this slot")
    ] = None

    async def start_domain_task(self, request: ScanRequest) -> bool:
        # FIXME
        # Handle old domain task if it exists
        if self.running_task is not None:
            self.running_task = None

        # Create new domain task
        self.running_task = Domain_Task.create(request.domain, request.session_id)

        # Run Task
        result = await self.running_task.begin()

        return result

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
