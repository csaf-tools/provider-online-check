from typing import Annotated
from pydantic import BaseModel, Field
from enum import Enum

from ..csaf.csaf_checker import CSAF_Checker
from ..database.domain_task_data import Domain_Task_Data

import os
import logging
import pickle
import time

logger = logging.getLogger(__name__)

CACHE_PATH_TASKS = "/app/store/tasks/"
CACHE_TIMEOUT_SECONDS=300

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

    skip_cache: Annotated[
        bool,
        Field(description="Skips cache if enabled/ guarantees to run csaf checker, even if the domain has recently been checked already")
    ] = False

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

        return result

    async def __write_to_cache(self):
        try:
            with open(f"/app/store/tasks/{self.data.cache_name}", "wb") as file:
                pickle.dump(self, file)

        except Exception as e:
            logger.error(f"Error writing domain task to file: {e}")

    async def __load_from_chache(self) -> Domain_Task_Data:
        if self.skip_cache:
            return None

        try:
            if not os.path.exists(f"{CACHE_PATH_TASKS}{self.data.cache_name}") :
                return None

            with open(f"{CACHE_PATH_TASKS}{self.data.cache_name}", 'rb') as file:
                task = pickle.load(file)

                # Cached task too old?
                if int(time.time()) - task.data.end_time > CACHE_TIMEOUT:
                    return None
                return task.data
        except Exception as e:
            logger.error(f"Error reading domain task from file: {e}")


    async def run_checker(self) -> bool:
        """
        Runs csaf checker asynchronously and stream its output
        into self.csaf_checker_output. This method updates status and returns
        True on successful run, False otherwise.

        Is serialized into cache on successful runs.
        If a domain task has been recently cached, it will be returned; skipping CSAF Checker
        """

        # Fetch and return cache
        cached_task_data = await self.__load_from_chache()
        if cached_task_data is not None:
            logger.info(f"Found {self.data.domain} in cache")
            self.data = cached_task_data
            return True

        # Start CSAF Checker
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

    def on_checker_done(self):
        self.data.end_time = int(time.time())

        # Write results to file cache
        await self.__write_to_cache()

        self.status = Domain_Task_Status.DONE

    def interrupt(self):
        self.status = Domain_Task_Status.INTERRUPTED

    def on_error(self, string):
        self.status = Domain_Task_Status.ERROR

        logger.error(f"Domain Task Error: {string}")
