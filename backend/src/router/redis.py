from __future__ import annotations

from typing import Annotated, Optional

import redis
from pydantic import Field

# Fields
BLOCKLIST_DB_FIELD = "blocklist:"


class Redis:
    _instance: Annotated[
        Optional[Redis], Field(description="Singleton instance")
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
        self._redis = redis.Redis(host='redis', port=6379, db=0)

    def is_session_id_in_blocklist(self, session_id: str, domain: str) -> bool:
        return self._redis.sismember(BLOCKLIST_DB_FIELD + domain, session_id)

    def block_session_id_for_domain(self, session_id: str, domain: str):
        if self.is_session_id_in_blocklist(session_id, domain):
            return
        self._redis.sadd(BLOCKLIST_DB_FIELD + domain, session_id)

    def unblock_session_id_for_domain(self, session_id: str, domain: str):
        self._redis.srem(BLOCKLIST_DB_FIELD + domain, session_id)
