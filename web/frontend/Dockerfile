FROM node:22-alpine

WORKDIR /app

COPY web/frontend/package.json web/frontend/package-lock.json ./
RUN npm ci

COPY web/frontend/ ./

EXPOSE 3000
CMD ["npm", "run", "dev"]
