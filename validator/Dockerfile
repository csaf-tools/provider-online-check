FROM node:22.21-alpine AS build

WORKDIR /app

## Installs

RUN npm install @secvisogram/csaf-validator-service
RUN npm ci

# Setup
EXPOSE 8082

COPY ./command.sh ./command.sh
RUN chmod -x ./command.sh

FROM build AS dev

## Command
CMD ["sh", "/app/command.sh"]

# FIXME
FROM nginx:1.29.4 AS prod

COPY --from=build /app/dist/client/browser /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/nginx.conf

CMD ["sh", "/app/command.sh"]
