<!--
SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
Software-Engineering: 2026 Intevation GmbH <https://intevation.de>

SPDX-License-Identifier: Apache-2.0
-->

## Answer

Response from backend to frontend when route /information/ is called

    {
        csaf_checker_version: string        // Version of the CSAF Checker used for this App
        csaf_validator_version: string      // Version of the CSAF Validator used for this App
        csaf_provider_version: string      / / Version of this app / the csaf provider
        docs: string      // API path to docs
        openapi: string      // API path to OpenAPI JSON file
    }
