#!/bin/bash

# Stop all development services

echo "🛑 Stopping all Gemini Enterprise services..."

supervisorctl -c /etc/supervisor/conf.d/supervisord.conf stop gemini-dev:*

echo "✅ All services stopped."