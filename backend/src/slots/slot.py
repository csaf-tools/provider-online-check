# Class representation of a CSAF checker / validator procedure
# Runs in its own thread. Communicates progress & results with
# a dedicated client object.
# Invokes database caching on success

# Involved in: 7, 8, 9, 12

from fastapi import FastAPI
from typing import Annotated
from pydantic import BaseModel, Fields, WithJsonSchema
from enum import Enum

from ..router.redis import get_redis

class Domain_Task_Status(Enum):
    UNDEFINED = 0          # No status set yet
    STARTED = 1            # On initialization
    RUNNING_CHECKER = 2    # Currently running csaf checker
    RUNNING_VALIDATOR = 3  # Currently running csaf validator
    DONE = 4               # Task is done
    PAUSED = 5             # Task has been paused
    INTERRUPTED = 6        # Task has been interrupted via controlled means
    ERROR = 7              # Task has failed due to an unintentional error


class Slot(BaseModel):
    running_task_id: Annotated[str, Field(description="Redis ID of currently running domain task for this slot")] 

class Domain_Task(BaseModel):
    status: Annotated[Domain_Task_Status, Field(description="Status of the scan request"), Field(default=Domain_Task_Status.UNDEFINED)]
    watching_clients: list[Annotated[str,  Field(description="List of session IDs for each client who is currently following this tasks progress")]]
    start_time: Annotated[int, Field(description="Timestamp of this tasks initiziation"), Field(gt=0)]
    domain: Annotated[string, Field(description="HTML domain that is queried")]

    csaf_checker_output: list[Annotated[str, Field(description="Log line printed by csaf checker")]]
    csaf_validator_output: list(Annotated[str, Field(description="Log line printed by csaf validator")])

    def is_orphaned(self) -> bool:
        # FIXME
        # Check if all watching_clients are disconnected
        return False
    
    def setup(self):
        status = Domain_Task_Status.STARTED
    
    def start_checker(self):
        status = Domain_Task_Status.RUNNING_CHECKER

    def start_validator(self):
        status = Domain_Task_Status.RUNNING_VALIDATOR

    def on_checker_done(self):
        # FIXME
        # Continue to validator either automatically or after user input
        status = Domain_Task_Status.DONE

    def on_validator_done(self):
        status = Domain_Task_Status.DONE
    
    def interrupt(self):
        status = Domain_Task_Status.INTERRUPTED
    
    def on_error(self):
        status = Domain_Task_Status.ERROR