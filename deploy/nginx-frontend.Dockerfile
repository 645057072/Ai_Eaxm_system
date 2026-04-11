# 构建前端静态资源并由 Nginx 提供；API 由同 compose 中 api 服务提供
FROM node:20-alpine AS fe
WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
ARG VITE_API_BASE=/api
ENV VITE_API_BASE=$VITE_API_BASE
RUN npm run build

FROM nginx:1.25-alpine
COPY deploy/nginx.combined.conf /etc/nginx/conf.d/default.conf
COPY --from=fe /app/frontend/dist /usr/share/nginx/html
