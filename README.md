# csaf-tools/provider-online-check

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

## Running the Application

We recommend using Docker to start the services:
```
docker compose up -d
```

In the README files of `backend` and `frontend`, you can find instructions on the components and how to run them without Docker.

## License

SPDX-License-Identifier: Apache-2.0

SPDX-FileCopyrightText: 2025 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
Software-Engineering: 2025 Intevation GmbH <https://intevation.de>
