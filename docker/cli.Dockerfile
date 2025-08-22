# Multi-stage Docker build for the Gemini CLI
# Optimized for minimal size and security

# Build arguments
ARG NODE_VERSION=20

# Container metadata labels
LABEL maintainer="Gemini Enterprise Team"
LABEL description="Gemini CLI Container"
LABEL version="1.0.0"
LABEL build-date=""
LABEL vcs-url="https://github.com/google-gemini/gemini-cli"

# Stage 1: Build environment
FROM node:${NODE_VERSION}-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    make \
    g++ \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy package files for better caching
COPY package.json package-lock.json ./
COPY packages/cli/package.json ./packages/cli/
COPY packages/core/package.json ./packages/core/
COPY packages/test-utils/package.json ./packages/test-utils/

# Install dependencies
RUN npm ci --workspaces --prefer-offline --no-audit

# Copy source code
COPY . .

# Build packages
RUN npm run build:packages

# Generate bundle
RUN npm run bundle

# Stage 2: Production image
FROM node:${NODE_VERSION}-slim as production

# Security labels
LABEL security.scan="enabled"
LABEL security.non-root="true"

# Set environment variables
ENV NODE_ENV=production \
    NPM_CONFIG_PREFIX=/usr/local/share/npm-global \
    PATH=$PATH:/usr/local/share/npm-global/bin \
    GEMINI_CLI_CONTAINER=true

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    make \
    g++ \
    curl \
    git \
    jq \
    bc \
    less \
    ripgrep \
    ca-certificates \
    tini \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r -g 1000 gemini && useradd -r -u 1000 -g gemini -m -s /bin/bash gemini

# Set up npm global package folder
RUN mkdir -p /usr/local/share/npm-global && \
    chown -R gemini:gemini /usr/local/share/npm-global

# Switch to non-root user
USER gemini

# Set working directory
WORKDIR /home/gemini

# Copy built CLI from builder stage
COPY --from=builder --chown=gemini:gemini /app/bundle /usr/local/share/npm-global/gemini-cli/

# Create symlink for gemini command
USER root
RUN ln -s /usr/local/share/npm-global/gemini-cli/gemini.js /usr/local/bin/gemini && \
    chmod +x /usr/local/share/npm-global/gemini-cli/gemini.js
USER gemini

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD gemini --version || exit 1

# Signal handling for graceful shutdown
STOPSIGNAL SIGTERM

# Use tini for proper signal handling
ENTRYPOINT ["tini", "--"]

# Default command
CMD ["gemini"]