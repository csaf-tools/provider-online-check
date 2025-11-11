# Validates a domain request. Checks if requested domain
# is valid
# Also checks if requested domain has a valid cache
# in database -> handles cache lookup

# Involved in: 4, 17, 18, 21

import re

# Basic domain validation pattern (same as before)
DOMAIN_PATTERN = (
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$"
)


def validate_domain(value: str) -> str:
    """
    Validate and normalize a domain string.

    - trims whitespace
    - rejects empty or None
    - checks simple domain regex

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
