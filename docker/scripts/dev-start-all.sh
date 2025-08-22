#!/bin/bash

# Start all development services

echo "🚀 Starting all Gemini Enterprise services..."

# Start supervisor and all services
supervisorctl -c /etc/supervisor/conf.d/supervisord.conf start gemini-dev:*

echo "✅ All services started. Use 'dev-status' to check status."
echo "📊 Logs available with 'dev-logs'"