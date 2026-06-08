# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

# Validates a domain request. Checks if requested domain
# is valid
# Also checks if requested domain has a valid cache
# in database -> handles cache lookup
import re

from ..database.valkey import Valkey_Controller

# Basic domain validation pattern (same as before)
DOMAIN_PATTERN = (
    r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
)

REQUEST_PATTERN = (
    rf"^(?:{DOMAIN_PATTERN}|https://{DOMAIN_PATTERN}"
    rf"(?:/[^/]+)*/provider-metadata\.json)$"
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
    if not re.match(REQUEST_PATTERN, v):
        raise ValueError(
            "Invalid domain/PMD format. Please enter a valid Domain or PMD URL. Domains require a non-zero length extension. PMDs must start with 'https://' and end with '/provider-metadata.json'"
        )

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

    # Valkey blocklist check
    if Valkey_Controller().is_domain_in_domain_blocklist(domain):
        raise ValueError("Session ID is blocked")

    return v
