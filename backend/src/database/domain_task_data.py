# This represents a data object for a specific domain task. It contains information about the domain as well as output from csaf checker and validator

from typing import Annotated, Dict, Any
from pydantic import BaseModel, Field
import time
import json


class Domain_Task_Data(BaseModel):
    domain: Annotated[str, Field(description="HTML domain that is queried")]
    start_time: Annotated[
        int, Field(description="Timestamp of this tasks initiziation")
    ]

    csaf_checker_output_runtime_log: list[
        Annotated[str, Field(description="Verbose output by csaf checker while it was running")]
    ] = []
    csaf_checker_output_result: Annotated[str, Field(description="Result of csaf checker")] = ""

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

    def results_to_json(self) -> Dict[str, Any]:
        return json.loads(self.csaf_checker_output_result)
