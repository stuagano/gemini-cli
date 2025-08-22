#!/bin/bash

# Start the agent server in development mode

echo "🚀 Starting Gemini Agent Server in development mode..."

# Activate virtual environment
source /home/developer/.venv/bin/activate

# Set development environment variables
export PYTHONPATH=/workspace
export PORT=${PORT:-8000}
export LOG_LEVEL=${LOG_LEVEL:-debug}
export APP_ENV=development

# Start the server with hot reload
echo "🔥 Starting server with hot reload on port $PORT..."
exec uvicorn src.api.agent_server:app \
    --host 0.0.0.0 \
    --port $PORT \
    --reload \
    --reload-dir src \
    --log-level $LOG_LEVEL