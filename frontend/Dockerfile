# Stage 1: Build SPA
FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

# Stage 2: Nginx runtime with auto-certs
FROM nginx:1.30-alpine
RUN apk add --no-cache openssl gettext
COPY frontend/nginx.conf.template /etc/nginx/templates/default.conf.template
COPY frontend/entrypoint.sh /entrypoint.sh
COPY --from=builder /app/dist /usr/share/nginx/html
RUN chmod +x /entrypoint.sh
EXPOSE 80 443
ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
