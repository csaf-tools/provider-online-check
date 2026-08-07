<!--
SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
Software-Engineering: 2026 Intevation GmbH <https://intevation.de>

SPDX-License-Identifier: Apache-2.0
-->

# Frontend Tests using Selenium

UI and integration tests for the CSAF Provider Scan.

## Prerequisites

- Python 3.11+
- Firefox browser installed
- Frontend and backend services running

## Setup

1. Install test dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure both frontend and backend are running:
```bash
# From project root
docker-compose up -d
```

The tests expect:
- Frontend running on: `http://localhost:48091`
- Backend running on: `http://localhost:48090`

## Running Tests

```bash
pytest
```
