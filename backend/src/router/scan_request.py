
from typing import Annotated
from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Self

from ..validators.client_validator import validate_client_blocklist_check
from ..validators.request_validator import validate_domain


class ScanRequest(BaseModel):
    session_id: Annotated[
        str,
        Field(description="Unique session id"),
    ]
    domain: Annotated[
        str,
        Field(description="Domain to scan for CSAF provider metadata"),
        Field(json_schema_extra={"example": "example.com"}),
    ]

    skip_cache: Annotated[
        bool,
        Field(description="Skips cache if enabled/ guarantees to run csaf checker, even if the domain has recently been checked already")
    ] = False

    @field_validator("domain")
    def _validate_domain(cls, value):
        """
        Validate domain for correctness.
        """
        # delegate validation to the external validator
        return validate_domain(value)

    @model_validator(mode="after")
    def _validate_session_in_blocklist(self) -> Self:
        """
        Validate session_id against the client blocklist for the given domain.
        """
        session_id = self.session_id
        domain = self.domain

        if session_id is None or domain is None:
            return self

        self.session_id = validate_client_blocklist_check(session_id, domain)

        return self
