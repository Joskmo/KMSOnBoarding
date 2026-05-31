# syntax=docker/dockerfile:1

# -------------------------------
# Stage 1: Build SPA
# -------------------------------
FROM node:24-alpine AS builder

WORKDIR /app

# Install dependencies (cached layer)
COPY package*.json ./
RUN npm ci && npm cache clean --force

# Copy source code
COPY . .

# Build args
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV NODE_ENV=production

RUN npm run build

# -------------------------------
# Stage 2: Nginx runtime
# -------------------------------
FROM nginx:1.30.2-alpine

# Install runtime dependencies
RUN apk add --no-cache openssl gettext

# Copy nginx template and entrypoint
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy built SPA from builder
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80 443

ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
