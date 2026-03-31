# This represents a data object for a specific domain task. It contains information about the domain as well as output from csaf checker and validator

import os
import time
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .domain_name_hash_wrapper import Domain_Name_Hash_Wrapper


class Domain_Task_Data(BaseModel):
    uuid: Annotated[
        UUID, Field(description="This tasks unique identifier", default_factory=uuid4)
    ]

    domain: Annotated[str, Field(description="HTML domain that is queried")]
    start_time: Annotated[
        int, Field(description="Timestamp of this tasks initiziation")
    ]
    end_time: Annotated[int, Field(description="Timestamp of this tasks finish")] = 0

    enable_validator: Annotated[
        bool,
        Field(description="Activates csaf validator for every downloaded document"),
    ] = True

    enable_validator_cache: Annotated[
        bool,
        Field(description="Caches validator results in file system"),
    ] = bool(os.environ.get("VALIDATOR_CACHE_RESULTS", "1"))

    validator_cache_file: Annotated[
        str, Field("Path to cache file created by csaf validator")
    ] = ""
    csaf_checker_output_runtime_log: list[
        Annotated[
            str,
            Field(description="Verbose output by csaf checker while it was running"),
        ]
    ] = []
    csaf_checker_output_result: Annotated[
        str, Field(description="Result of csaf checker")
    ] = ""

    cache_lifetime: Annotated[
        int,
        Field(
            description="Time in seconds in which a recorded task is considered to fresh to be rerun automatically"
        ),
    ] = int(os.environ.get("CACHE_TIMEOUT_SECONDS", "300"))

    @classmethod
    def create(cls, domain: str) -> "Domain_Task_Data":
        data = {
            "domain": domain,
            "start_time": int(time.time()),
        }
        return cls(**data)

    def get_domain_hash(self) -> str:
        return Domain_Name_Hash_Wrapper().domain_hash(self.domain)

    def cache_is_outdated(self) -> bool:
        """
        Used to check if this task is too old to be considered cached
        """
        return int(time.time()) - self.end_time > self.cache_lifetime
