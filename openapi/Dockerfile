FROM node:25-alpine

WORKDIR /app

COPY ./dev.js dev.js
COPY ./package.json package.json

RUN npm i -D openapi-typescript

ENTRYPOINT [ "node", "dev.js" ]

