
import redis
import os

REDIS_URL= os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis = redis.from_url(REDIS_URL, decode_responses=True)

# Fields
BLOCKLIST_DB_FIELD="blocklist"

def get_redis() -> redis:
    return redis

def is_session_id_in_blocklist(session_id: str) -> bool:
    return get_redis().sismember(BLOCKLIST_DB_FIELD, session_id)