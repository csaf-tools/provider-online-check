# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import os
from typing import Annotated, Optional

import valkey
from pydantic import Field

from .domain_task_data import Domain_Task_Data

logger = logging.getLogger(__name__)

# Fields
ENV_DOMAIN_BLOCKLIST = "DOMAIN_BLOCKLIST"

BLOCKLIST_CLIENT_DB_FIELD = "blocklist-client:"
BLOCKLIST_DOMAIN_DB_FIELD = "blocklist-domain"
RECORDED_DOMAIN_TASK_BY_DOMAIN = "domain-task:"
RECORDED_DOMAIN_TASK_BY_UUID = "domain-task-id-to-domain:"


class Valkey_Controller:
    _instance: Annotated[
        Optional[Valkey_Controller], Field(description="Singleton instance")
    ] = None

    _cache_lifetime: Annotated[
        int,
        Field(description="Lifetime of a valkey cache entry before expiry"),
    ] = int(os.environ.get("CACHE_TIMEOUT_SECONDS", "604800"))

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Avoid reinitialization
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

        # Setup Valkey, use RESP 3 features (https://valkey-py.readthedocs.io/en/latest/resp3_features.html)
        self._valkey = valkey.Valkey(host="valkey", port=6379, db=0, protocol=3)

        # Clear blocked domains
        if self._valkey.exists(BLOCKLIST_DOMAIN_DB_FIELD):
            self._valkey.delete(BLOCKLIST_DOMAIN_DB_FIELD)

        # Inject blocked domains from env file
        blocked_domains = os.getenv(ENV_DOMAIN_BLOCKLIST, "")
        for domain in blocked_domains.split():
            success = self.block_domain(domain)
            if not success:
                logger.error(
                    f"Blocked Domain Injection: Domain {domain} has already been blocked. Does {ENV_DOMAIN_BLOCKLIST} contain duplicates?"
                )

    # Cached Domain Tasks
    # This links a domain tasks uuid to the persistent cache file of its data
    def record_domain_task(self, task: Domain_Task_Data):
        # Save task as json blob
        json = task.model_dump_json()

        # Connect json with task uuid and hashed domain name
        self._valkey.set(
            RECORDED_DOMAIN_TASK_BY_DOMAIN + task.get_domain_hash(),
            json,
            ex=self._cache_lifetime,
        )
        self._valkey.set(
            RECORDED_DOMAIN_TASK_BY_UUID + str(task.uuid), json, ex=self._cache_lifetime
        )

    def get_domain_task_by_uuid(self, uuid: str) -> Domain_Task_Data:
        if not self._valkey.exists(RECORDED_DOMAIN_TASK_BY_UUID + str(uuid)):
            return None

        json = self._valkey.get(RECORDED_DOMAIN_TASK_BY_UUID + str(uuid))
        return Domain_Task_Data.model_validate_json(json)

    def get_domain_task_by_domain_hash(self, domain_hash: str) -> Domain_Task_Data:
        if not self._valkey.exists(RECORDED_DOMAIN_TASK_BY_DOMAIN + domain_hash):
            return None

        json = self._valkey.get(RECORDED_DOMAIN_TASK_BY_DOMAIN + domain_hash)
        return Domain_Task_Data.model_validate_json(json)

    # Client Blocklist

    def is_session_id_in_client_blocklist(self, session_id: str, domain: str) -> bool:
        return (
            self._valkey.sismember(BLOCKLIST_CLIENT_DB_FIELD + domain, session_id) == 1
        )

    def block_session_id_for_domain(self, session_id: str, domain: str) -> bool:
        if self.is_session_id_in_client_blocklist(session_id, domain):
            return False
        self._valkey.sadd(BLOCKLIST_CLIENT_DB_FIELD + domain, session_id)
        return True

    def unblock_session_id_for_domain(self, session_id: str, domain: str):
        self._valkey.srem(BLOCKLIST_CLIENT_DB_FIELD + domain, session_id)

    # Domain Blocklist

    def is_domain_in_domain_blocklist(self, domain: str) -> bool:
        return self._valkey.sismember(BLOCKLIST_DOMAIN_DB_FIELD, domain) == 1

    def block_domain(self, domain: str) -> bool:
        if self.is_domain_in_domain_blocklist(domain):
            return False
        self._valkey.sadd(BLOCKLIST_DOMAIN_DB_FIELD, domain)
        return True

    def unblock_domain(self, domain: str):
        self._valkey.srem(BLOCKLIST_DOMAIN_DB_FIELD, domain)
