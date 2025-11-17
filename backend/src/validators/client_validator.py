# Validates a requesting client against blacklist and various DoS
# security checks

# Involved in: 4, 19, 20, 21

from ..router.redis import Redis


def validate_client_blocklist_check(session_id: str, domain: str) -> str:
    """
    Checks blocklist status of session id

    Throws authentication error, if session id is blocked

    Returns session id as is
    """
    if session_id is None:
        raise ValueError("Session ID cannot be empty")

    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("Session ID cannot be empty")

    # Redis blocklist check
    # FIXME
    if Redis().is_session_id_in_blocklist(session_id, domain):
        raise ValueError("Session ID is blocked")

    return session_id
