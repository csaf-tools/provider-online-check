# csaf-tools/provider-online-check

## Introduction

A web application, which allows to check a CSAF trusted provider online.

Status: _early development_

Aim:

 * Help organizations to analyse and improve their own CSAF providers.
   Expected to be useful during the initial setup of a provider.

 * Check third party providers to see if they have problems
   (from time to time).

 * Make it easier to run the `csaf_checker`.


Considerations:

 * It is planned to offer this as a service (with limited resources).

 * Large CSAF providers will run this for themselfes, e.g. using a prepared
   image for deployment.

 * When in doubt, too much stress on the CSAF Providers will be prevented.

## Getting started

### Get the repository

```shell
git clone https://github.com/csaf-tools/provider-online-check/
cd provider-online-check
```

### Running the Application

We recommend using Docker to start the services:

```shell
docker compose up -d
```

In the README files of `backend` and `frontend`, you can find instructions on the components and how to run them without Docker.

## How to use

Visit http://localhost:48091/ in your browser.

## Developing

For local development with hot-reloading, use `docker compose up -d` which mounts the source directories into the containers. Changes to the code will be reflected immediately without rebuilding.

To run linting and tests, use the provided Makefile targets:

```shell
make lint      # Run black, isort, flake8 on backend code
make run-tests # Run pytest on backend tests
```

See the README files in [backend/](backend/) and [frontend/](frontend/) for component-specific development instructions.

## Architecture

The application consists of three main components:

- **Frontend**: A Vue.js 3 single-page application using Bootstrap for styling. It provides the user interface for initiating scans and viewing results.
- **Backend**: A FastAPI-based REST API that handles scan requests. It exposes endpoints for starting scans and checking status. The interactive API documentation is available at `/api/docs`.
- **Redis**: Used as a message broker for the job queue, for asynchronous scan job processing

## Security Considerations

The CSAF Provider Online check tool retrieves lots of documents from remote locations.
To minimize the impact on the network on the source and destination servers and networks, the tool provides settings for throttling and limiting the scanning.

Keep in mind, that the CSAF Provider Online check tool, and it's component (the CSAF Checker and Validator) process untrusted CSAF documents.
If testing untrusted CSAF providers, it is recommended to run the tool only in containers and with restricted network access.

## Contributing

#### Commit message convention

This repository uses the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) standard for commit messages.

## Dependencies

### With Docker (recommended)

- [Docker](https://docs.docker.com/get-docker/) with Docker Compose

### Without Docker

#### Backend
- Python 3.10+
- Redis
- Python packages: FastAPI, uvicorn, pydantic, redis, rq (see [backend/requirements.txt](backend/requirements.txt))

#### Frontend
- Node.js 18+
- npm or yarn
- Vue 3, Vite, Bootstrap, Axios (see [frontend/package.json](frontend/package.json))

## Production Deployment

### Environment Variables

All variables are configured in the `.env` file in the project root.
Docker Compose reads this file automatically.

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT_BACKEND` | `48090` | Host port for the backend API. |
| `PORT_FRONTEND` | `48091` | Host port for the frontend. |
| `SCAN_SLOTS` | `10` | Maximum number of concurrent scans. |
| `FOOTER_TEXT` | _empty_ | Custom HTML content appended to the footer of the frontend. |

Example `.env`:

```
PORT_BACKEND=8080
PORT_FRONTEND=8081
SCAN_SLOTS=5
FOOTER_TEXT=Hosted by <a href="https://example.com">Example Corp</a>
```

### Reverse Proxy

In production, place a reverse proxy in front of the services to terminate TLS and route traffic.
Below is a minimal example using Apache httpd serving frontend and backend.

```apache
<VirtualHost *:443>
    ServerName scan.example.com

    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/scan.example.com.crt
    SSLCertificateKeyFile /etc/ssl/private/scan.example.com.key

    # Security headers
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-Content-Type-Options "nosniff"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
    Header always set Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'"

    # Backend API
    ProxyPass /api http://localhost:48090/api
    ProxyPassReverse /api http://localhost:48090/api

    # Frontend (catch-all)
    ProxyPass / http://localhost:48091/
    ProxyPassReverse / http://localhost:48091/
</VirtualHost>
```

Enable the required modules:

```shell
a2enmod proxy proxy_http ssl headers
systemctl reload apache2
```

### Restrict Network Access

The application allows users to scan external targets.
To prevent data exfiltration, restrict the access to internal and forbidden networks.

### Production Docker Images

Production Dockerfiles are provided for both services.
Use `docker-compose.prod.yml` to build and run them:

```shell
docker compose -f docker-compose.prod.yml up -d --build
```

## License

SPDX-License-Identifier: Apache-2.0

SPDX-FileCopyrightText: 2025 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
Software-Engineering: 2025 Intevation GmbH <https://intevation.de>
