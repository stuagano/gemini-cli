#!/bin/bash

# Start the BMAD Agent Server

echo "Starting BMAD Agent Server..."
echo "================================"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Set environment variables
export BMAD_PROJECT_ROOT=$(pwd)
export PYTHONPATH="${PYTHONPATH}:${BMAD_PROJECT_ROOT}/src"

# Check if required packages are installed
echo "Upgrading build tools..."
python -m pip install --upgrade pip setuptools wheel
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to install dependencies. Please check your Python environment."
    exit 1
fi

# Kill any process that may be listening on port 2000
echo "Checking for existing process on port 2000..."
PID=$(lsof -t -i:2000)
if [ ! -z "$PID" ]; then
    echo "Found existing process with PID $PID. Terminating..."
    kill -9 $PID
    sleep 1 # Give the OS a moment to release the port
fi

# Start the server
echo "Starting server on http://localhost:2000"
echo "API Documentation: http://localhost:2000/docs"
echo "Press Ctrl+C to stop the server"
echo "================================"

cd src/api
python -m uvicorn agent_server:app --host 0.0.0.0 --port 2000 --reload --log-level info