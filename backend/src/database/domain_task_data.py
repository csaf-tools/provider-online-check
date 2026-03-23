# This represents a data object for a specific domain task. It contains information about the domain as well as output from csaf checker and validator

from typing import Annotated, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

import time
import json
import hashlib

class Domain_Task_Data(BaseModel):
    uuid: Annotated[UUID, Field(description="This tasks unique identifier", default_factory=uuid4)]

    domain: Annotated[str, Field(description="HTML domain that is queried")]
    start_time: Annotated[int, Field(description="Timestamp of this tasks initiziation")]
    end_time: Annotated[int, Field(description="Timestamp of this tasks finish")] = 0
    enable_validator: Annotated[bool, Field(description="Activates csaf validator for every downloaded document")] = True

    validator_cache_file: Annotated[str, Field("Path to cache file created by csaf validator")] = ""
    csaf_checker_output_runtime_log: list[
        Annotated[str, Field(description="Verbose output by csaf checker while it was running")]
    ] = []
    csaf_checker_output_result: Annotated[str, Field(description="Result of csaf checker")] = ""

    @classmethod
    def create(cls, domain: str) -> "Domain_Task_Data":
        data = {
            "domain": domain,
            "start_time": int(time.time()),
        }
        return cls(**data)

    def results_to_json(self) -> Dict[str, Any]:
        return json.loads(self.csaf_checker_output_result)


    def domain_hash(self) -> str:
        return hashlib.sha256(self.domain.encode("utf-8")).hexdigest()

