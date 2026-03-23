# Saves and loads cached results of csaf checker & validator

# Involved in: 9, 18

from __future__ import annotations
from typing import Annotated, Optional
from pydantic import Field

from .redis import Redis_Controller

import logging
import os
import pickle
import time
import hashlib

from ..database.domain_task_data import Domain_Task_Data

logger = logging.getLogger(__name__)

CACHE_TIMEOUT_SECONDS=300

class Database_Manager():
    _instance: Annotated[
        Optional[Database_Manager], Field(description="Singleton instance")
    ] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def write_task(self, task: Domain_Task_Data):
        Redis_Controller().record_domain_task(task)

    def __evaluate_cache_time(self, data: Domain_Task_Data) -> Domain_Task_Data:
        if data is not None:
            # Cached task too old?
            if int(time.time()) - data.end_time > CACHE_TIMEOUT_SECONDS:
                return None

            return task.data
        return None

    def load_task_by_domain(self, domain: str) -> Domain_Task_Data:
        data = Redis_Controller().get_domain_task_by_domain_hash(domain)

        return self.__evaluate_cache_time(data)

    def load_task_by_id(self, uuid: str) -> Domain_Task_Data:
        data = Redis().get_domain_task_by_uuid(domain)

        return self.__evaluate_cache_time(data)
