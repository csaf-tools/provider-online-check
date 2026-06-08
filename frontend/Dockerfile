# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

# --- Dev target ---
FROM node:24.14-alpine AS dev

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 8080

# with hot-reloading
CMD ["npm", "run", "dev"]

# --- Prod stages ---

# Build frontend assets
FROM dev AS build

RUN npm ci

ARG VITE_BACKEND_PORT
ARG VITE_FOOTER_TEXT
RUN npm run build

# Production image
FROM httpd:2-alpine AS prod

COPY --from=build /app/dist /usr/local/apache2/htdocs/
COPY httpd.conf /usr/local/apache2/conf/httpd.conf

EXPOSE 8080

CMD ["httpd-foreground"]
