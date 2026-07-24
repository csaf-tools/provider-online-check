# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated, Optional

from pydantic import BaseModel, Field


class SlotStatusEntry(BaseModel):
    id: Annotated[int, Field(description="Slot ID")]
    available: Annotated[bool, Field(description="If available / has a task")]
    domain: Annotated[Optional[str], Field(description="Domain being checked")] = None
    status: Annotated[Optional[str], Field(description="Scan status")] = None
    start_time: Annotated[Optional[int], Field(description="Task start timestamp")] = None
    files_checked: Annotated[Optional[int], Field(description="Number of files checked")] = None
    latest_file_checked: Annotated[Optional[str], Field(description="Last checked file URL")] = None


class AdminStatusResponse(BaseModel):
    slots: Annotated[list[SlotStatusEntry], Field(description="State of all scan slots")]
