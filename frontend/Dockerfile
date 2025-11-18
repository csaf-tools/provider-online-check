FROM node:alpine

WORKDIR /app

COPY . .

RUN npm install

EXPOSE 8080

# with hot-reloading
CMD ["npm", "run", "dev"]
