# Class representation of a CSAF checker / validator procedure
# Runs in its own thread. Communicates progress & results with
# a dedicated client object.
# Invokes database caching on success

# Involved in: 7, 8, 9, 12

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field

# from ..router.redis import get_redis
from ..router.scan_request import ScanRequest


class Domain_Task_Status(Enum):
    UNDEFINED = 0  # No status set yet
    STARTED = 1  # On initialization
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
        Field(default=Domain_Task_Status.UNDEFINED),
    ]
    watching_clients: list[
        Annotated[
            str,
            Field(
                description="List of session IDs for each client who is currently following this tasks progress"
            ),
        ]
    ]
    start_time: Annotated[
        int, Field(description="Timestamp of this tasks initiziation"), Field(gt=0)
    ]
    domain: Annotated[str, Field(description="HTML domain that is queried")]

    csaf_checker_output: list[
        Annotated[str, Field(description="Log line printed by csaf checker")]
    ]
    csaf_validator_output: list[
        Annotated[str, Field(description="Log line printed by csaf validator")]
    ]

    # A task is considered orphaned, if each listener to this task has disconnected for a while
    def is_orphaned(self) -> bool:
        # Listener is considered disconnected if connection couldn't be established within this time period (in seconds)
        # disconnection_timeout_grace_period = 10

        # FIXME
        # Check if all watching_clients are disconnected

        return False

    def setup(self):
        self.status = Domain_Task_Status.STARTED

    def start_checker(self):
        self.status = Domain_Task_Status.RUNNING_CHECKER

    def start_validator(self):
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
    ] = ""

    def start_domain_task(self, request: ScanRequest) -> bool:
        return True

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
