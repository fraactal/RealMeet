FROM node:22-alpine

WORKDIR /app

COPY --chown=node:node package.json .
COPY --chown=node:node package-lock.json .
COPY --chown=node:node tsconfig.json .
COPY --chown=node:node tsconfig.app.json .
COPY --chown=node:node vite.config.ts .
COPY --chown=node:node postcss.config.js .
COPY --chown=node:node tailwind.config.js .
COPY --chown=node:node index.html .

RUN npm ci

COPY --chown=node:node . .

RUN mkdir -p /app/dist
RUN chown -R node:node /app

USER node

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
