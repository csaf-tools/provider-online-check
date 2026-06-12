# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

# Wrapper around a Domain Task
# Interface for Slot Manager and Domain Tasks
# May or may not have a running Domain Task

import asyncio
import logging
from typing import Annotated

from pydantic import BaseModel, Field

# from ..router.valkey import get_valkey
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
            return (
                ScanResponseStatus.ERROR,
                self.running_task.error_message or "A backend error occurred",
            )
        elif self.running_task.get_status() == Domain_Task_Status.INTERRUPTED:
            return ScanResponseStatus.ERROR, "Task has been stopped manually"
        elif self.running_task.get_status() == Domain_Task_Status.DONE:
            return ScanResponseStatus.DONE_CHECKER, ""
        elif (
            len(self.running_task.get_data(False).csaf_checker_output_runtime_log) == 0
        ):
            return ScanResponseStatus.INITIALIZED, ""

        return ScanResponseStatus.RUNNING_CHECKER, ""
