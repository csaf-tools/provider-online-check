from pydantic import BaseModel, Field


class ScanResponse(BaseModel):
    # Dummy structure
    status: str = Field(..., description="Status of the scan request")
    domain: str = Field(..., description="Domain being scanned")
    slot_id: int = Field(..., description="Slot id the domain task is performed in")
    message: str = Field(..., description="Additional information about the scan")
