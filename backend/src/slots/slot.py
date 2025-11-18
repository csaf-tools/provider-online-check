# Class representation of a CSAF checker / validator procedure
# Runs in its own thread. Communicates progress & results with
# a dedicated client object.
# Invokes database caching on success

# Involved in: 7, 8, 9, 12

from enum import Enum
from typing import Annotated
from pydantic import BaseModel, Field
import asyncio
import time

# from ..router.redis import get_redis
from ..router.scan_request import ScanRequest

CSAF_BINARY_PATH = "../../bin/csaf-binary/bin-linux-amd64/"
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
    start_time: Annotated[
        int, Field(description="Timestamp of this tasks initiziation"), Field(gt=0)
    ]
    domain: Annotated[str, Field(description="HTML domain that is queried")]

    csaf_checker_output: list[
        Annotated[str, Field(description="Log line printed by csaf checker")]
    ] = []
    csaf_validator_output: list[
        Annotated[str, Field(description="Log line printed by csaf validator")]
    ] = []

    @classmethod
    def create(cls, domain: str, session_id: str) -> "Domain_Task":
        data = {
            "domain": domain,
            "watching_clients": [session_id],
            "start_time": int(time.time()),
            "status": Domain_Task_Status.INITIALIZED
        }
        return cls(**data)

    # A task is considered orphaned, if each listener to this task has disconnected for a while
    def is_orphaned(self) -> bool:
        # Listener is considered disconnected if connection couldn't be established within this time period (in seconds)
        # disconnection_timeout_grace_period = 10

        # FIXME
        # Check if all watching_clients are disconnected

        return False

    async def start_checker(self) -> bool:
        """
        Runs csaf checker asynchronously and stream its output
        into self.csaf_checker_output. This method updates status and returns
        True on successful run, False otherwise.
        """
        self.status = Domain_Task_Status.RUNNING_CHECKER

        csaf_checker_path = CSAF_BINARY_PATH + CSAF_CHECKER_BINARY

        try:
            # create subprocess, merge stderr into stdout for unified streaming
            task_checker = await asyncio.create_subprocess_exec(
                csaf_checker_path,
                ["--verbose"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=CSAF_BINARY_PATH,
                env="",
            )

            # Stream output lines as they come
            assert task_checker.stdout is not None
            while True:
                line = await task_checker.stdout.readline()
                if not line:
                    break
                decoded = line.decode(errors="replace").rstrip("\n")
                # append to logs
                self.csaf_checker_output.append(decoded)

                # FIXME
                # Notify client socket

            returncode = await task_checker.wait()

            # On normal completion, call on_checker_done (which currently sets DONE)
            if returncode == 0:
                self.on_checker_done()
                return True
            else:
                # record non-zero exit code and mark error
                self.csaf_checker_output.append(f"CSAF Checker exited with code {returncode}")
                self.on_error()
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
            self.csaf_checker_output.append(f"CSAF Checker Binary not found: {csaf_checker_path}")
            self.on_error()
            return False

        except Exception as e:
            # Unexpected error running the process
            self.csaf_checker_output.append(f"CSAF Checker error: {e}")
            self.on_error()
            return False

    async def start_validator(self):
        self.status = Domain_Task_Status.RUNNING_VALIDATOR

    def on_checker_done(self):
        # FIXME
        # Continue to validator either automatically or after user input
        self.status = Domain_Task_Status.DONE

    def on_validator_done(self):
        self.status = Domain_Task_Status.DONE

    def interrupt(self):
        self.status = Domain_Task_Status.INTERRUPTED

    def on_error(self):
        self.status = Domain_Task_Status.ERROR


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

        # CSAF Checker
        result = await self.running_task.start_checker()

        # CSAF Validator
        result = await self.running_task.start_validator()

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
