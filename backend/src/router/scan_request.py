from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, validator

class ScanRequest(BaseModel):
    session_id: str = Field(
        description="Unique session id"
    )
    domain: str = Field(
        ...,
        description="Domain to scan for CSAF provider metadata",
        example="example.com",
    )

    @validator("domain", pre=True)
    def _validate_domain(cls, v):
        # delegate validation to the external validator
        return validate_domain(v)


    @validator("session_id", pre=True)
    def _validate_client_blocklist_check(cls, v):
        # delegate validation to the external validator
        return validate_client_blocklist_check(v)
