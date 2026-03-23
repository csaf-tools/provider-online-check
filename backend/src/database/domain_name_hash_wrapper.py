# This is a small utility wrapper to convert a domain name into a hash string

from __future__ import annotations
from typing import Annotated, Optional
from pydantic import Field

import hashlib

class Domain_Name_Hash_Wrapper():
    _instance: Annotated[
        Optional[Domain_Name_Hash_Wrapper], Field(description="Singleton instance")
    ] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def domain_hash(self, domain_name: str) -> str:
        return hashlib.sha256(domain_name.encode("utf-8")).hexdigest()

