# Validates a domain request. Checks if requested domain
# is valid
# Also checks if requested domain has a valid cache
# in database -> handles cache lookup

# Involved in: 4, 17, 18, 21

import re

from ..database.redis import Redis

# Basic domain validation pattern (same as before)
DOMAIN_PATTERN = (
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$"
)


def validate_domain(value: str) -> str:
    """
    Validate and normalize a domain string.

    Returns the trimmed domain on success or raises ValueError on failure.
    """
    if value is None:
        raise ValueError("Domain cannot be empty")

    if not isinstance(value, str) or not value.strip():
        raise ValueError("Domain cannot be empty")

    v = value.strip()
    if not re.match(DOMAIN_PATTERN, v):
        raise ValueError("Invalid domain format")

    return v


def validate_domain_blocklist_check(domain: str) -> str:
    """
    Check if domain is blocklisted generally

    Returns the trimmed domain on success or raises ValueError on failure.
    """
    if domain is None:
        raise ValueError("Domain cannot be empty")

    if not isinstance(domain, str) or not domain.strip():
        raise ValueError("Domain cannot be empty")

    v = domain.strip()

    # Redis blocklist check
    if Redis().is_domain_in_domain_blocklist(domain):
        raise ValueError("Session ID is blocked")

    return v
