FROM node:25-alpine

WORKDIR /app

COPY ./main.js main.js
COPY ./package.json package.json

RUN npm i -D openapi-typescript

ENTRYPOINT [ "node", "main.js" ]

