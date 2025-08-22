#!/bin/bash

# View development logs

case "${1:-all}" in
    "agent"|"agent-server")
        echo "📋 Viewing Agent Server logs..."
        tail -f /workspace/logs/agent-server.log
        ;;
    "cli")
        echo "📋 Viewing CLI development logs..."
        tail -f /workspace/logs/cli-dev.log
        ;;
    "typescript"|"ts")
        echo "📋 Viewing TypeScript watch logs..."
        tail -f /workspace/logs/typescript-watch.log
        ;;
    "supervisor")
        echo "📋 Viewing Supervisor logs..."
        tail -f /workspace/logs/supervisord.log
        ;;
    "all")
        echo "📋 Viewing all logs..."
        tail -f /workspace/logs/*.log
        ;;
    *)
        echo "Usage: dev-logs [agent|cli|typescript|supervisor|all]"
        exit 1
        ;;
esac