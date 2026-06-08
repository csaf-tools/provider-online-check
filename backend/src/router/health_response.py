# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Annotated[
        str,
        Field(description="'healthy' or 'unhealthy'"),
    ]

    free_slots: Annotated[
        int,
        Field(description="Number of available scan slots"),
    ]

    total_slots: Annotated[
        int,
        Field(description="Total number of scan slots"),
    ]

    csaf_checker_available: Annotated[
        bool,
        Field(description="Whether the csaf_checker binary is available"),
    ]

    valkey_available: Annotated[
        bool,
        Field(description="Whether Valkey is available"),
    ]

    validator_available: Annotated[
        bool,
        Field(description="Whether Validator is available"),
    ]

    errors: Annotated[
        Optional[list[str]],
        Field(default=None, description="List of error messages if unhealthy"),
    ]
