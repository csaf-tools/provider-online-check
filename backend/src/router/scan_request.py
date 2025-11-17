from pydantic import BaseModel, Field, validator, model_validator

from ..validators.client_validator import validate_client_blocklist_check
from ..validators.request_validator import validate_domain


class ScanRequest(BaseModel):
    session_id: str = Field(description="Unique session id")
    domain: str = Field(
        ...,
        description="Domain to scan for CSAF provider metadata",
        example="example.com",
    )

    @validator("domain", pre=True)
    def _validate_domain(cls, value):
        """
        Validate domain for correctness.
        """
        # delegate validation to the external validator
        return validate_domain(value)

    @model_validator(mode='after')
    def _validate_session_in_blocklist(cls, values):
        """
        Validate session_id against the client blocklist for the given domain.
        """
        session_id = values.session_id
        domain = values.domain

        if session_id is None or domain is None:
            return values

        values.session_id = validate_client_blocklist_check(session_id, domain)

        return values
