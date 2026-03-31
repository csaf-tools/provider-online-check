from __future__ import annotations

import logging
from typing import Annotated, Optional

import redis
from pydantic import Field

from .domain_task_data import Domain_Task_Data

logger = logging.getLogger(__name__)

# Fields
BLOCKLIST_CLIENT_DB_FIELD = "blocklist-client:"
BLOCKLIST_DOMAIN_DB_FIELD = "blocklist-domain:"
RECORDED_DOMAIN_TASK_BY_DOMAIN = "domain-task:"
RECORDED_DOMAIN_TASK_BY_UUID = "domain-task-id-to-domain:"


class Redis_Controller:
    _instance: Annotated[
        Optional[Redis_Controller], Field(description="Singleton instance")
    ] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Avoid reinitialization
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

        # Setup Redis
        self._redis = redis.Redis(host="redis", port=6379, db=0)

    # Cached Domain Tasks
    # This links a domain tasks uuid to the persistent cache file of its data
    def record_domain_task(self, task: Domain_Task_Data):
        # Save task as json blob
        json = task.model_dump_json()

        # Connect json with task uuid and hashed domain name
        self._redis.set(RECORDED_DOMAIN_TASK_BY_DOMAIN + task.get_domain_hash(), json)
        self._redis.set(RECORDED_DOMAIN_TASK_BY_UUID + str(task.uuid), json)

    def get_domain_task_by_uuid(self, uuid: str) -> Domain_Task_Data:
        if not self._redis.exists(RECORDED_DOMAIN_TASK_BY_UUID + str(uuid)):
            return None

        json = self._redis.get(RECORDED_DOMAIN_TASK_BY_UUID + str(uuid))
        return Domain_Task_Data.model_validate_json(json)

    def get_domain_task_by_domain_hash(self, domain_hash: str) -> Domain_Task_Data:
        if not self._redis.exists(RECORDED_DOMAIN_TASK_BY_DOMAIN + domain_hash):
            return None

        json = self._redis.get(RECORDED_DOMAIN_TASK_BY_DOMAIN + domain_hash)
        return Domain_Task_Data.model_validate_json(json)

    # Client Blocklist

    def is_session_id_in_client_blocklist(self, session_id: str, domain: str) -> bool:
        return self._redis.sismember(BLOCKLIST_CLIENT_DB_FIELD + domain, session_id) == 1

    def block_session_id_for_domain(self, session_id: str, domain: str) -> bool:
        if self.is_session_id_in_client_blocklist(session_id, domain):
            return False
        self._redis.sadd(BLOCKLIST_CLIENT_DB_FIELD + domain, session_id)
        return True

    def unblock_session_id_for_domain(self, session_id: str, domain: str):
        self._redis.srem(BLOCKLIST_CLIENT_DB_FIELD + domain, session_id)

    # Domain Blocklist

    def is_domain_in_domain_blocklist(self, domain: str) -> bool:
        return self._redis.sismember(BLOCKLIST_DOMAIN_DB_FIELD + domain, 1) == 1

    def block_domain(self, domain: str) -> bool:
        if self.is_domain_in_domain_blocklist(domain):
            return False
        self._redis.sadd(BLOCKLIST_DOMAIN_DB_FIELD + domain, 1)
        return True

    def unblock_domain(self, domain: str):
        self._redis.srem(BLOCKLIST_DOMAIN_DB_FIELD + domain, 1)
