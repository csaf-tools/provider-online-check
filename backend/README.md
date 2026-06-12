<!--
SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
Software-Engineering: 2026 Intevation GmbH <https://intevation.de>

SPDX-License-Identifier: Apache-2.0
-->

# CSAF Provider Scan Backend

FastAPI-based backend.

## Setup

The backend is intended to be used in conjunction with the frontend and validator containers.
Refer to the main `README.md` for setup information.

## API Reference

### `POST /api/scan/start`

Initiates a CSAF provider scan for the given domain.

**HTTP Status**: `201 Created` on success, `500 Internal Server Error` on failure.

#### Request Body

See `docs/payload.md` for more info

```json
{
  "session_id": "0",
  "domain": "example.com",
  "start_at_line": 0,
  "max_lines": 10,
  "prioritize_newest_lines": true,
  "skip_cache": false,
  "clear_any_running": false
}
```

#### Response Body

See `docs/domain_task_answer.md` for more info

```json
{
  "domain": "example.com",
  "status": "DONE_CHECKER",
  "slot_id": 0,
  "error": "",
  "runtime_output": [""],
  "results_checker": "",
  "files_checked": 0,
  "latest_file_checked": ""
}
```

### `GET /api/information`

Returns version and metadata about the running provider instance.

#### Response Body

See `docs/information_answer.md` for more info

```json
{
  "csaf_checker_version": "1.0.0",
  "csaf_validator_version": "1.0.0",
  "csaf_provider_version": "1.0.0",
  "docs": "/api/docs",
  "openapi": "/api/openapi.json"
}
```

### `GET /api/health`

Returns the health status of the backend and its dependencies, such as valkey and the validator container.

**HTTP Status**: `200 OK` if healthy, `503 Service Unavailable` if any component is unhealthy.

#### Response Body

```json
{
  "status": "healthy",
  "free_slots": 10,
  "total_slots": 10,
  "csaf_checker_available": true,
  "valkey_available": true,
  "validator_available": true
}
```
