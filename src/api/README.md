# BMAD Agent Server API

## Overview

The BMAD Agent Server provides a REST and WebSocket API for the TypeScript CLI to interact with Python-based agents. This is the critical bridge that connects the Gemini CLI frontend with the Enterprise Architect agent system.

## Components

### 1. **agent_server.py**
- Main FastAPI application
- REST endpoints for agent requests
- WebSocket support for streaming
- Health checks and metrics

### 2. **router.py**
- Intelligent request routing to appropriate agents
- Natural language intent analysis
- Multi-agent workflow orchestration

### 3. **websocket_handler.py**
- Real-time bidirectional communication
- Streaming response support
- Event subscriptions
- Connection management

### 4. **queue_broker.py**
- Priority-based task queuing
- Concurrency management
- Result caching
- Retry logic

## Quick Start

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### Start the Server

```bash
# From project root
python src/start_server.py
```

The server will start on `http://localhost:8000`

### Test the Server

```bash
# In another terminal
python src/test_server.py
```

## API Endpoints

### Health Check
```http
GET /api/v1/health
```

### List Agents
```http
GET /api/v1/agents
```

### Agent Request
```http
POST /api/v1/agent/request
Content-Type: application/json

{
  "type": "analyst",
  "action": "research",
  "payload": {
    "query": "Analyze market trends"
  },
  "context": {}
}
```

### Batch Requests
```http
POST /api/v1/agent/batch
Content-Type: application/json

[
  {"type": "scout", "action": "analyze", ...},
  {"type": "developer", "action": "generate", ...}
]
```

## WebSocket Interface

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/agent/stream');

// Initialize
ws.send(JSON.stringify({
  type: 'init',
  metadata: { client: 'gemini-cli' }
}));
```

### Streaming Request
```javascript
ws.send(JSON.stringify({
  type: 'stream_request',
  request: {
    type: 'developer',
    action: 'generate_code',
    payload: { ... }
  }
}));
```

## Agent Types

- **analyst**: Market research, competitive analysis
- **pm**: Product management, PRD creation
- **architect**: System design, GCP service selection
- **developer**: Code generation, implementation
- **qa**: Testing, quality assurance
- **scout**: Codebase analysis, DRY enforcement
- **po**: Product ownership, value optimization

## Development

### Run with Auto-reload
```bash
uvicorn src.api.agent_server:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation
Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Architecture

```
TypeScript CLI (packages/cli)
    ↓ HTTP/WebSocket
FastAPI Server (src/api/agent_server.py)
    ↓ Routes via Router
Agent Registry → Enhanced Agents
    ↓ Processes via Nexus
Response → Queue → WebSocket → CLI
```

## Configuration

The server uses environment variables for configuration:

```bash
# Server config
BMAD_HOST=0.0.0.0
BMAD_PORT=8000
BMAD_LOG_LEVEL=info

# Agent config
BMAD_MAX_CONCURRENT=10
BMAD_MAX_PER_AGENT=3
BMAD_TIMEOUT=30

# Optional: Vertex AI config
GCP_PROJECT=your-project
GCP_REGION=us-central1
```

## Error Handling

All errors return consistent JSON format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "timestamp": "2024-01-20T10:30:00Z"
  }
}
```

## Next Steps

1. **TypeScript Client**: Create the client in `packages/cli/src/agents/`
2. **Process Manager**: Implement Python process management from TypeScript
3. **Authentication**: Add API key or OAuth support
4. **Rate Limiting**: Implement request throttling
5. **Monitoring**: Add Prometheus metrics

## Troubleshooting

### Server won't start
- Check Python version (3.8+ required)
- Verify all dependencies installed
- Check port 8000 is available

### Agents not responding
- Verify agent files exist in `src/agents/enhanced/`
- Check agent initialization in server logs
- Ensure unified_agent_base.py is properly configured

### WebSocket disconnects
- Check firewall/proxy settings
- Verify WebSocket support in client
- Monitor server logs for errors