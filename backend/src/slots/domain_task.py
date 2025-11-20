from typing import Annotated
from pydantic import BaseModel, Field
from enum import Enum

from ..csaf.csaf_checker import CSAF_Checker
from ..database.domain_task_data import Domain_Task_Data

import logging

logger = logging.getLogger(__name__)


class Domain_Task_Status(Enum):
    UNDEFINED = 0  # No status set yet
    INITIALIZED = 1  # On initialization
    RUNNING_CHECKER = 2  # Currently running csaf checker
    RUNNING_VALIDATOR = 3  # Currently running csaf validator
    DONE = 4  # Task is done
    PAUSED = 5  # Task has been paused
    INTERRUPTED = 6  # Task has been interrupted via controlled means
    ERROR = 7  # Task has failed due to an unintentional error


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
        Field(description="Data concerning this domain task. Will be saved persistently on task completion")
    ] = None

    @classmethod
    def create(cls, domain: str, session_id: str) -> "Domain_Task":
        data = {
            "data": Domain_Task_Data.create(domain),
            "watching_clients": [session_id],
            "status": Domain_Task_Status.INITIALIZED,
        }
        return cls(**data)

    # A task is considered orphaned, if each listener to this task has disconnected for a while
    def is_orphaned(self) -> bool:
        # Listener is considered disconnected if connection couldn't be established within this time period (in seconds)
        # disconnection_timeout_grace_period = 10

        # FIXME
        # Check if all watching_clients are disconnected

        return False

    async def begin(self) -> bool:

        result = await self.run_checker()
        if result is False:
            return result

        result = await self.run_validator()

        return result

    async def run_checker(self) -> bool:
        """
        Runs csaf checker asynchronously and stream its output
        into self.csaf_checker_output. This method updates status and returns
        True on successful run, False otherwise.
        """
        self.status = Domain_Task_Status.RUNNING_CHECKER
        csaf_checker = CSAF_Checker()
        try:
            result = await csaf_checker.run(self.data)

            if result is True:
                self.on_checker_done()
                return True
            else:
                self.on_error("CSAF Checker exited")
                return False

        except Exception as e:
            # Unexpected error running the process
            self.on_error(f"Domain Task Error while running CSAF Checker: {e}")
            return False

    async def run_validator(self):
        self.status = Domain_Task_Status.RUNNING_VALIDATOR

        self.on_validator_done()

    def on_checker_done(self):
        # FIXME
        # Continue to validator either automatically or after user input
        self.status = Domain_Task_Status.DONE

    def on_validator_done(self):
        self.status = Domain_Task_Status.DONE

    def interrupt(self):
        self.status = Domain_Task_Status.INTERRUPTED

    def on_error(self, string):
        self.status = Domain_Task_Status.ERROR

        logger.error(f"Domain Task Error: {string}")
