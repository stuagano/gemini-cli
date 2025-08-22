#!/bin/bash

# Check status of development services

echo "📊 Gemini Enterprise Development Services Status:"
echo "=============================================="

supervisorctl -c /etc/supervisor/conf.d/supervisord.conf status

echo ""
echo "🌐 Service URLs:"
echo "- Agent Server: http://localhost:8000"
echo "- Agent Server API Docs: http://localhost:8000/docs"
echo "- CLI Development: Interactive terminal"
echo ""
echo "📁 Log files:"
ls -la /workspace/logs/