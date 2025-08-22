# All-in-One Development Container for Gemini Enterprise Architect
# Includes Python, Node.js, development tools, and hot reload capabilities

# Build arguments
ARG PYTHON_VERSION=3.11
ARG NODE_VERSION=20

# Container metadata labels
LABEL maintainer="Gemini Enterprise Team"
LABEL description="Gemini Enterprise Development Environment"
LABEL version="1.0.0"
LABEL build-date=""
LABEL vcs-url="https://github.com/google-gemini/gemini-cli"

# Base image with both Python and Node.js
FROM python:${PYTHON_VERSION}-slim as base

# Security labels
LABEL security.scan="enabled"
LABEL security.non-root="true"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/workspace \
    NODE_ENV=development \
    NPM_CONFIG_PREFIX=/usr/local/share/npm-global \
    PATH=$PATH:/usr/local/share/npm-global/bin \
    DEBIAN_FRONTEND=noninteractive \
    SHELL=/bin/bash

# Install Node.js from official NodeSource repository
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - && \
    apt-get update && apt-get install -y --no-install-recommends \
    # Node.js and npm
    nodejs \
    # Build tools
    build-essential \
    make \
    g++ \
    # Development tools
    git \
    curl \
    wget \
    unzip \
    vim \
    nano \
    jq \
    bc \
    less \
    tree \
    htop \
    # Network tools
    netcat-openbsd \
    telnet \
    # Security and certificates
    ca-certificates \
    gnupg \
    lsb-release \
    # Process management
    supervisor \
    tini \
    # Search tools
    ripgrep \
    # Python development
    python3-dev \
    python3-pip \
    # Database clients (for development)
    postgresql-client \
    redis-tools \
    # Additional utilities
    procps \
    psmisc \
    lsof \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Python development tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
    # Development tools
    black \
    flake8 \
    mypy \
    pytest \
    pytest-asyncio \
    pytest-cov \
    # Code quality
    bandit \
    safety \
    # Hot reload for FastAPI
    uvicorn[standard] \
    watchdog \
    # Jupyter for interactive development
    jupyter \
    ipython \
    # Debugging
    pdb \
    ipdb

# Install global npm packages for development
RUN npm install -g \
    # TypeScript tools
    typescript \
    ts-node \
    # Development tools
    nodemon \
    concurrently \
    # Code quality
    eslint \
    prettier \
    # Build tools
    esbuild \
    # Testing
    vitest \
    # Package management
    npm-check-updates

# Create development user
RUN groupadd -r -g 1000 developer && \
    useradd -r -u 1000 -g developer -m -s /bin/bash developer && \
    usermod -aG sudo developer

# Create workspace directory
WORKDIR /workspace

# Set up npm global directory
RUN mkdir -p /usr/local/share/npm-global && \
    chown -R developer:developer /usr/local/share/npm-global

# Create supervisor configuration for hot reload
COPY docker/configs/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy development scripts
COPY docker/scripts/ /usr/local/bin/
RUN chmod +x /usr/local/bin/*.sh

# Set up development environment
RUN mkdir -p /workspace/logs /workspace/data /workspace/cache && \
    chown -R developer:developer /workspace

# Switch to development user
USER developer

# Create Python virtual environment
RUN python -m venv /home/developer/.venv && \
    echo "source /home/developer/.venv/bin/activate" >> /home/developer/.bashrc

# Set up shell environment
RUN echo 'export PS1="\[\033[01;32m\]dev@gemini\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ "' >> /home/developer/.bashrc && \
    echo 'alias ll="ls -la"' >> /home/developer/.bashrc && \
    echo 'alias la="ls -A"' >> /home/developer/.bashrc && \
    echo 'alias l="ls -CF"' >> /home/developer/.bashrc

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose development ports
EXPOSE 8000 3000 5173 8080 9229

# Signal handling for graceful shutdown
STOPSIGNAL SIGTERM

# Use tini for proper signal handling
ENTRYPOINT ["tini", "--"]

# Default command starts supervisor for multi-process development
CMD ["/usr/local/bin/dev-entrypoint.sh"]