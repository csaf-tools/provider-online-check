# Saves and loads cached results of csaf checker & validator

# Involved in: 9, 18

from __future__ import annotations

import logging
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

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def write_task(self, task: Domain_Task_Data):
        Redis_Controller().record_domain_task(task)

    def load_task_by_domain(self, domain: str) -> Domain_Task_Data:
        data = Redis_Controller().get_domain_task_by_domain_hash(
            Domain_Name_Hash_Wrapper().domain_hash(domain)
        )

        return data

    def load_task_by_id(self, uuid: str) -> Domain_Task_Data:
        data = Redis_Controller().get_domain_task_by_uuid(uuid)

        return data
