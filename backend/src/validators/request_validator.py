# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

# Validates a domain request. Checks if requested domain
# is valid
# Also checks if requested domain has a valid cache
# in database -> handles cache lookup

import re
from urllib.parse import urlsplit, urlunsplit

from ..database.valkey import Valkey_Controller

# Basic domain validation pattern (same as before)
DOMAIN_PATTERN = (
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
)

REQUEST_PATTERN = (
    rf"^(?:{DOMAIN_PATTERN}|https://{DOMAIN_PATTERN}"
    rf"(?:/[^/]+)*/provider-metadata\.json)$"
)


def _normalize_hostname(hostname: str) -> str:
    """Lowercase hostnames and convert them to Punycode"""
    try:
        # idna encoding returns bytes, then convert back to string
        return hostname.lower().encode("idna").decode("ascii")
    except (UnicodeError, UnicodeDecodeError):
        return hostname.lower()


def validate_domain(value: str) -> str:
    """
    Validate and normalize a scan target.

    Normalizatios on the domain or PMD URL:
    - Remove whitespace at start & end

    Normalizations on the domain:
    - Strip surrounding whitespace
    - Lowercase the hostname and protocol scheme
    - Convert IDN hostnames to Punycode

    Returns the normalized domain on success or raises ValueError on failure.
    """
    if value is None:
        raise ValueError("Domain cannot be empty")

    if not isinstance(value, str) or not value.strip():
        raise ValueError("Domain cannot be empty")

    v = value.strip()
    parts = urlsplit(v)

    if parts.scheme:  # PMD URL
        # the protocol scheme is lower-cased implicitly
        v = urlunsplit(parts._replace(netloc=_normalize_hostname(parts.netloc)))
    else:  # Domain
        v = _normalize_hostname(v)

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
