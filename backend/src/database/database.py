# Saves and loads cached results of csaf checker & validator

# Involved in: 9, 18

from __future__ import annotations

import logging
import os
import time
from typing import Annotated, Optional

from pydantic import Field

from ..database.domain_task_data import Domain_Task_Data
from .domain_name_hash_wrapper import Domain_Name_Hash_Wrapper
from .redis import Redis_Controller

logger = logging.getLogger(__name__)


class Database_Manager:
    _instance: Annotated[
        Optional[Database_Manager], Field(description="Singleton instance")
    ] = None

    cache_lifetime: Annotated[
        int,
        Field(
            description="Time in seconds in which a recorded task is considered to fresh to be rerun automatically"
        ),
    ] = int(os.environ.get("DATABASE_CACHE_TIMEOUT_SECONDS", "300"))

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def write_task(self, task: Domain_Task_Data):
        Redis_Controller().record_domain_task(task)

    def __evaluate_cache_time(self, data: Domain_Task_Data) -> Domain_Task_Data:
        if data is not None:
            # Cached task too old?
            if int(time.time()) - data.end_time > self.cache_lifetime:
                logger.info(
                    f"Cache was found for {data.domain} but outdated: {data.end_time}"
                )
                return None

            return data
        return None

    def load_task_by_domain(self, domain: str) -> Domain_Task_Data:
        data = Redis_Controller().get_domain_task_by_domain_hash(
            Domain_Name_Hash_Wrapper().domain_hash(domain)
        )

        return self.__evaluate_cache_time(data)

    def load_task_by_id(self, uuid: str) -> Domain_Task_Data:
        data = Redis_Controller().get_domain_task_by_uuid(uuid)

        return self.__evaluate_cache_time(data)
