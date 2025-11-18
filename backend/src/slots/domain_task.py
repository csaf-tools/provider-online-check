from typing import Annotated
from pydantic import BaseModel, Field
from enum import Enum

from ..database.csaf_domain_task_data import CSAF_Domain_Task_Data

import asyncio
import logging
import os

logger = logging.getLogger(__name__)

CSAF_BINARY_PATH = "./bin/csaf-binary/bin-linux-amd64/"
CSAF_CHECKER_BINARY = "csaf_checker"
CSAF_VALIDATOR_BINARY = "csaf_validator"


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
        CSAF_Domain_Task_Data,
        Field(description="Data concerning this domain task. Will be saved persistently on task completion")
    ] = None

    @classmethod
    def create(cls, domain: str, session_id: str) -> "Domain_Task":
        data = {
            "data": CSAF_Domain_Task_Data.create(domain),
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

        csaf_checker_path = CSAF_BINARY_PATH + CSAF_CHECKER_BINARY

        try:
            # create subprocess, merge stderr into stdout for unified streaming
            args = ["--verbose", self.data.domain]
            task_checker = await asyncio.create_subprocess_exec(
                os.path.abspath(csaf_checker_path),
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=CSAF_BINARY_PATH,
                env=None,
            )
            logger.info("Async task started")

            # Stream output lines as they come
            assert task_checker.stdout is not None
            while True:
                line = await task_checker.stdout.readline()
                if not line:
                    break
                decoded = line.decode(errors="replace").rstrip("\n")
                # append to logs
                self.data.csaf_checker_output.append(decoded)
                logger.info(decoded)

                # FIXME
                # Notify client socket

            logger.info("Task done")
            returncode = await task_checker.wait()
            logger.info(f"Task has returncode {returncode}")

            # On normal completion, call on_checker_done (which currently sets DONE)
            if returncode == 0:
                self.on_checker_done()
                return True
            else:
                # record non-zero exit code and mark error
                self.on_error(f"CSAF Checker exited with code {returncode}")
                return False

        except asyncio.CancelledError:
            # If the coroutine is cancelled, try to terminate the process
            try:
                task_checker.terminate()
            except Exception:
                pass
            self.interrupt()
            raise  # re-raise so callers know cancellation happened

        except FileNotFoundError:
            # binary not found
            self.on_error(f"CSAF Checker Binary not found: {csaf_checker_path}")
            return False

        except Exception as e:
            # Unexpected error running the process
            self.on_error(f"CSAF Checker error: {e}")
            return False

    async def run_validator(self):
        self.status = Domain_Task_Status.RUNNING_VALIDATOR

        self.on_validator_done

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
