# ==========================================
# SplashScreen Dockerfile (React + Vite + Nginx)
# Multi-stage production build
# ==========================================

# Stage 1: Build the React application
FROM node:22-alpine AS builder

WORKDIR /app

# Vite embeds VITE_* variables into bundle at build time
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy source and build static bundle
COPY . ./
RUN npm run build

# Stage 2: Serve with lightweight Nginx
# nginx:alpine is not executable in the current Docker Desktop Linux engine.
# Use the Debian-based runtime image instead.
FROM nginx:stable

# Keep a small HTTP client for the container health check.
RUN apt-get update \
    && apt-get install --no-install-recommends -y curl \
    && rm -rf /var/lib/apt/lists/*

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled assets from build stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

# Health check for Nginx server
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD curl --fail --silent http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
