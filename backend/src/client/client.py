# Used as communication interface with frontend

# Forwards Error, Progress and Result Messages
# Involved in: 5, 10, 15

from pydantic import BaseModel, Field


class ScanResponse(BaseModel):
    # Dummy structure
    status: str = Field(..., description="Status of the scan request")
    domain: str = Field(..., description="Domain being scanned")
    message: str = Field(..., description="Additional information about the scan")
