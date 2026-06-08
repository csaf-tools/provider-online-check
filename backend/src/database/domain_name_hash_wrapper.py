# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

# This is a small utility wrapper to convert a domain name into a hash string

from __future__ import annotations

import hashlib
from typing import Annotated, Optional

from pydantic import Field


class Domain_Name_Hash_Wrapper:
    _instance: Annotated[
        Optional[Domain_Name_Hash_Wrapper], Field(description="Singleton instance")
    ] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def domain_hash(self, domain_name: str) -> str:
        return hashlib.sha256(domain_name.encode("utf-8")).hexdigest()
