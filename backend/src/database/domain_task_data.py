# This represents a data object for a specific domain task. It contains information about the domain as well as output from csaf checker and validator

from typing import Annotated
from pydantic import BaseModel, Field
import time


class Domain_Task_Data(BaseModel):
    domain: Annotated[str, Field(description="HTML domain that is queried")]
    start_time: Annotated[
        int, Field(description="Timestamp of this tasks initiziation")
    ]

    csaf_checker_output: list[
        Annotated[str, Field(description="Log line printed by csaf checker")]
    ] = []
    csaf_validator_output: list[
        Annotated[str, Field(description="Log line printed by csaf validator")]
    ] = []

    @classmethod
    def create(cls, domain: str) -> "Domain_Task_Data":
        data = {
            "domain": domain,
            "start_time": int(time.time()),
        }
        return cls(**data)
