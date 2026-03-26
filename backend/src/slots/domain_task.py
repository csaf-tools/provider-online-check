import logging
import os
import time
from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, Field

from ..csaf.csaf_checker import CSAF_Checker
from ..database.database import Database_Manager
from ..database.domain_task_data import Domain_Task_Data

logger = logging.getLogger(__name__)


class Domain_Task_Status(Enum):
    UNDEFINED = 0  # No status set yet
    INITIALIZED = 1  # On initialization
    RUNNING_CHECKER = 2  # Currently running csaf checker
    DONE = 3  # Task is done
    PAUSED = 4  # Task has been paused
    INTERRUPTED = 5  # Task has been interrupted via controlled means
    ERROR = 6  # Task has failed due to an unintentional error


class Domain_Task(BaseModel):
    status: Annotated[
        Domain_Task_Status,
        Field(description="Status of the scan request"),
    ] = Domain_Task_Status.UNDEFINED

    data: Annotated[
        Optional[Domain_Task_Data],
        Field(
            description="Data concerning this domain task. Will be saved persistently on task completion"
        ),
    ] = None

    csaf_checker: Annotated[
        Optional[CSAF_Checker],
        Field(description="Wrapper for asynchroniously running csaf checker task"),
    ] = None

    latest_visit: Annotated[
        int,
        Field(
            description="Records the latest timestamp when a request for data has been sent to this domain task. This timestamp will be used to determine, if this domain task has been orphaned or not"
        ),
    ] = 0

    time_before_orphaned: Annotated[
        int,
        Field(
            description="Time in seconds a task can run with out active listeners before being considered orphaned"
        ),
    ] = int(os.environ.get("TASK_TIME_BEFORE_ORPHANED", "50"))

    @classmethod
    def create(cls, domain: str, session_id: str) -> "Domain_Task":
        data = {
            "data": Domain_Task_Data.create(domain),
            "status": Domain_Task_Status.INITIALIZED,
            "latest_visit": int(time.time()),
        }
        return cls(**data)

    def update_visit_time(self):
        self.latest_visit = int(time.time())

    async def run_checker(self):
        """
        Runs csaf checker asynchronously and awaits return type

        Is serialized into cache on successful runs.
        """
        self.update_visit_time()

        # Generate validator path
        self.get_data(False).validator_cache_file = self.get_data(False).get_domain_hash()

        # Start CSAF Checker
        self.status = Domain_Task_Status.RUNNING_CHECKER

        self.csaf_checker = CSAF_Checker()
        code, err = await self.get_csaf_checker().run(self.get_data(False))

        if code == 0:
            self.on_checker_done()
        elif code == 1:
            self.on_error(err)
        elif code == 2:
            self.on_interrupt()

        self.csaf_checker = None

    def get_csaf_checker(self) -> CSAF_Checker:
        return self.csaf_checker

    def get_data(self, internal: bool) -> Domain_Task_Data:
        """
        Returns data object. Also updates last visit time, if called from a non-internal process.
        All processes are internal, except those that propapage the data back to a user via API
        """
        if not internal:
            self.update_visit_time()
        return self.data

    def stop_task(self):
        self.update_visit_time()
        if self.get_csaf_checker() is None:
            return

        self.get_csaf_checker().stop()

    def restart_task(self):
        self.update_visit_time()
        if self.get_csaf_checker() is None:
            return

        self.get_csaf_checker().restart()

    def pause_task(self):
        self.update_visit_time()
        if self.get_csaf_checker() is None:
            return

        self.get_csaf_checker().pause()

    def unpause_task(self):
        self.update_visit_time()
        if self.get_csaf_checker() is None:
            return

        self.get_csaf_checker().unpause()

    def on_checker_done(self):
        self.get_data(False).end_time = int(time.time())

        # Write results to file cache
        Database_Manager().write_task(self.data)

        self.status = Domain_Task_Status.DONE

    def on_interrupt(self):
        self.status = Domain_Task_Status.INTERRUPTED

    def on_error(self, string):
        self.status = Domain_Task_Status.ERROR

        logger.error(f"Domain Task Error: {string}")

    def get_status(self) -> Domain_Task_Status:
        return self.status

    # Returns false if domain task has been interrupted or is in an erroneous state
    def is_in_valid_state(self) -> bool:
        # Split up to appease linters
        if self.status == Domain_Task_Status.INTERRUPTED:
            return False
        if self.status == Domain_Task_Status.ERROR:
            return False
        return True

    # A domain task is considered orphaned, if the last time any request has been sent to this domain task (including getting data) has
    # taken longer than a predefined time
    def is_orphaned(self) -> bool:
        return int(time.time()) - self.latest_visit > self.time_before_orphaned
