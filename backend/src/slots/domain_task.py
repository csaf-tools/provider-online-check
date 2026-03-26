import logging
import time
from enum import Enum
from typing import Annotated

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
    watching_clients: Annotated[
        list[str],
        Field(
            description="List of session IDs for each client who is currently following this tasks progress"
        ),
    ] = Field(default_factory=list)

    data: Annotated[
        Domain_Task_Data,
        Field(
            description="Data concerning this domain task. Will be saved persistently on task completion"
        ),
    ] = None

    @classmethod
    def create(cls, domain: str, session_id: str) -> "Domain_Task":
        data = {
            "data": Domain_Task_Data.create(domain),
            "watching_clients": [session_id],
            "status": Domain_Task_Status.INITIALIZED,
        }
        return cls(**data)

    async def run_checker(self):
        """
        Runs csaf checker asynchronously and awaits return type

        Is serialized into cache on successful runs.
        """

        # Generate validator path
        self.data.validator_cache_file = self.data.get_domain_hash()

        # Start CSAF Checker
        self.status = Domain_Task_Status.RUNNING_CHECKER

        csaf_checker = CSAF_Checker()
        code, err = await csaf_checker.run(self.data)

        if code == 0:
            self.on_checker_done()
        elif code == 1:
            self.on_error(err)
        elif code == 2:
            self.interrupt()

    def on_checker_done(self):
        self.data.end_time = int(time.time())

        # Write results to file cache
        Database_Manager().write_task(self.data)

        self.status = Domain_Task_Status.DONE

    def interrupt(self):
        self.status = Domain_Task_Status.INTERRUPTED

    def on_error(self, string):
        self.status = Domain_Task_Status.ERROR

        logger.error(f"Domain Task Error: {string}")

    # Returns false if domain task has been interrupted or is in an erroneous state
    def is_in_valid_state(self) -> bool:
        # Split up to appease linters
        if self.status == Domain_Task_Status.INTERRUPTED:
            return False
        if self.status == Domain_Task_Status.ERROR:
            return False
        return True

    # A domain task is considered orphaned, if each listener to this task has disconnected for a while
    def is_orphaned(self) -> bool:
        # Listener is considered disconnected if connection couldn't be established within this time period (in seconds)
        # disconnection_timeout_grace_period = 10

        # FIXME
        # Check if all watching_clients are disconnected

        return False
