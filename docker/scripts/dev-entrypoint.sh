#!/bin/bash

# Development environment entrypoint script
# Sets up the development environment and starts services

set -e

echo "🚀 Starting Gemini Enterprise Development Environment..."

# Create log directory if it doesn't exist
mkdir -p /workspace/logs

# Activate Python virtual environment if it exists
if [ -f "/home/developer/.venv/bin/activate" ]; then
    source /home/developer/.venv/bin/activate
    echo "✅ Python virtual environment activated"
fi

# Install Python dependencies if requirements.txt exists and packages aren't installed
if [ -f "/workspace/requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    pip install -r /workspace/requirements.txt
    echo "✅ Python dependencies installed"
fi

# Install Node.js dependencies if package.json exists
if [ -f "/workspace/package.json" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
    echo "✅ Node.js dependencies installed"
fi

# Build TypeScript packages if they exist
if [ -f "/workspace/package.json" ] && grep -q "build:packages" /workspace/package.json; then
    echo "🔨 Building TypeScript packages..."
    npm run build:packages
    echo "✅ TypeScript packages built"
fi

# Start services based on command line arguments
case "${1:-interactive}" in
    "agent-server")
        echo "🔧 Starting Agent Server only..."
        exec python src/start_server.py
        ;;
    "cli")
        echo "🔧 Starting CLI development only..."
        exec npm run start
        ;;
    "all")
        echo "🔧 Starting all services with supervisor..."
        # Start all services
        supervisorctl -c /etc/supervisor/conf.d/supervisord.conf start gemini-dev:*
        exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
        ;;
    "supervisor")
        echo "🔧 Starting supervisor without auto-starting services..."
        exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
        ;;
    "interactive"|"bash")
        echo "🔧 Starting interactive bash shell..."
        echo "Available commands:"
        echo "  dev-start-agent     - Start agent server"
        echo "  dev-start-cli       - Start CLI development"
        echo "  dev-start-all       - Start all services"
        echo "  dev-stop-all        - Stop all services"
        echo "  dev-logs            - View all logs"
        echo "  dev-status          - Check service status"
        exec /bin/bash
        ;;
    *)
        echo "🔧 Executing custom command: $*"
        exec "$@"
        ;;
esac