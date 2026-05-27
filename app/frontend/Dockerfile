# Frontend image: SPA build served by nginx.
# Этап 1 — сборка React-приложения.
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Этап 2 — nginx раздаёт собранный SPA, медиа и статику, проксирует API/WS.
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
