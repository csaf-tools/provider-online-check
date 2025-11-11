# Used as communication interface with frontend

# Forwards Error, Progress and Result Messages
# Involved in: 5, 10, 15

from typing import Annotated

from pydantic import BaseModel, Field, Required


class ScanResponse(BaseModel):
    # Dummy structure
    status: Annotated[str, Field(description="Status of the scan request")] = Required
    domain: Annotated[str, Field(description="Domain being scanned")] = Required
    message: Annotated[
        str, Field(description="Additional information about the scan")
    ] = Required
