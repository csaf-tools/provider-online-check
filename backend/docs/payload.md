<!--
SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
Software-Engineering: 2026 Intevation GmbH <https://intevation.de>

SPDX-License-Identifier: Apache-2.0
-->

## Payload

Send from frontend to backend


    {
        // Required
        domain: string      // URL domain to check
        session_id: string  // Unique client session id (like UUID to identify client)

        // Optional
        ignore_cache: bool  // Client wants to check a domain, regardless of database cache. Default: False
        interrupt: bool     // Client interrupts their request, effectively stopping backend. Default: False
        enable_validator: bool // Runs CSAF Validator for every document downloaded by CSAF Checker. Default: True

        // Output Shortening
        start_at_line: int  // Earliest output entry to retrieve. Default: 0
        max_lines: int      // Maximum lines to output. Set to -1 to get all lines. Default: 10
        prioritize_newest_lines: bool // Output newest lines first. Default: True
    }
