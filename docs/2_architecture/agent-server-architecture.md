# Agent Server Architecture

## Overview

The Gemini Enterprise Architect employs a dual-process architecture that separates the user interface and file management (TypeScript/Node.js CLI) from the intelligent agent processing (Python/FastAPI server). This document explains the architecture, communication patterns, and the critical role of the agent server in the system.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Responsibilities](#component-responsibilities)
3. [Communication Patterns](#communication-patterns)
4. [Agent Capabilities](#agent-capabilities)
5. [Operational Modes](#operational-modes)
6. [Performance Characteristics](#performance-characteristics)
7. [Deployment Considerations](#deployment-considerations)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
│                    (Terminal/IDE/Web Browser)                    │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Gemini CLI (TypeScript/Node.js)                │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐│
│  │   React/Ink UI   │  │  Command Parser  │  │  File System   ││
│  │   - Interactive  │  │  - Natural Lang  │  │  - Read/Write  ││
│  │   - Real-time    │  │  - Slash Cmds    │  │  - Watch       ││
│  └──────────────────┘  └──────────────────┘  └────────────────┘│
│                                                                   │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                    HTTP/WebSocket Client                      ││
│  │         - Agent communication                                 ││
│  │         - Real-time updates                                   ││
│  │         - Fallback handling                                   ││
│  └──────────────────────────────────────────────────────────────┘│
└────────────────────────────┬─────────────────────────────────────┘
                             │
                    HTTP/WebSocket (Port 2000)
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Agent Server (Python/FastAPI)                    │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                     FastAPI Application                       ││
│  │  - REST endpoints (/api/v1/*)                                ││
│  │  - WebSocket server (/ws)                                    ││
│  │  - Health monitoring (/health)                               ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                   │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                    Nexus Core Orchestrator                    ││
│  │  - Agent routing                                             ││
│  │  - Workflow management                                       ││
│  │  - Context sharing                                           ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                   │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                    Specialized AI Agents                      ││
│  │                                                               ││
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           ││
│  │  │  Scout  │ │Architect│ │Guardian │ │Developer│           ││
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘           ││
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐                       ││
│  │  │   PM    │ │   PO    │ │   QA    │                       ││
│  │  └─────────┘ └─────────┘ └─────────┘                       ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                   │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                     Supporting Services                       ││
│  │  - Code Analysis (AST)                                       ││
│  │  - Pattern Detection                                         ││
│  │  - Security Scanning                                         ││
│  │  - Performance Profiling                                     ││
│  │  - Knowledge Base (RAG)                                      ││
│  └──────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Gemini CLI (TypeScript/Node.js)

**Primary Responsibilities:**
- User interface and interaction
- File system operations
- Command parsing and validation
- Session management
- Real-time display updates
- Extension integration (VS Code, IDE)

**Key Features:**
- React-based terminal UI with Ink
- Natural language command processing
- File watching and hot reload
- Multi-format output support
- Theme customization

### Agent Server (Python/FastAPI)

**Primary Responsibilities:**
- Intelligent code analysis
- Multi-agent orchestration
- Pattern detection and matching
- Security vulnerability scanning
- Performance bottleneck detection
- Architectural recommendations

**Key Features:**
- 7 specialized AI agents with unique capabilities
- Parallel task execution
- AST-based code analysis
- Machine learning integration
- Knowledge base management

## Communication Patterns

### 1. HTTP REST API

**Endpoint Structure:**
```
POST /api/v1/agent/execute
POST /api/v1/agent/scout/analyze
POST /api/v1/agent/guardian/validate
GET  /api/v1/health
GET  /api/v1/metrics
```

**Request Flow:**
```typescript
// CLI Request
{
  "agent": "scout",
  "task": "check_duplicates",
  "input": {
    "code": "function authenticate(user, password) {...}",
    "file_path": "src/auth/login.js",
    "context": {
      "project_type": "web_app",
      "language": "javascript"
    }
  }
}

// Server Response
{
  "status": "success",
  "agent": "scout",
  "result": {
    "duplicates_found": true,
    "similar_implementations": [
      {
        "file": "src/auth/existing-auth.js",
        "similarity": 0.92,
        "lines": [45, 67]
      }
    ],
    "recommendations": ["Reuse existing auth module"],
    "execution_time_ms": 234
  }
}
```

### 2. WebSocket Real-time Updates

**Connection:** `ws://localhost:2000/ws`

**Message Types:**
```typescript
// Status Update
{
  "type": "status_update",
  "data": {
    "agent": "guardian",
    "status": "scanning",
    "progress": 45
  }
}

// Validation Warning
{
  "type": "validation_warning",
  "data": {
    "severity": "high",
    "message": "SQL injection vulnerability detected",
    "file": "src/db/queries.js",
    "line": 23
  }
}

// Agent Collaboration
{
  "type": "agent_collaboration",
  "data": {
    "from": "scout",
    "to": "architect",
    "message": "Found existing pattern, suggesting reuse"
  }
}
```

## Agent Capabilities

### Scout Agent
- **Duplication Detection**: Identifies similar code patterns across the codebase
- **Code Quality Analysis**: Measures complexity, maintainability
- **Technical Debt Assessment**: Identifies areas needing refactoring
- **Dependency Analysis**: Maps module dependencies

### Architect Agent
- **System Design**: Recommends architectural patterns (MVC, Microservices, etc.)
- **Technology Selection**: Suggests appropriate tech stack
- **Scalability Planning**: Identifies potential bottlenecks
- **Integration Design**: Plans API and service integrations

### Guardian Agent
- **Security Scanning**: Detects vulnerabilities (SQL injection, XSS, etc.)
- **Continuous Validation**: Real-time monitoring of code changes
- **Compliance Checking**: Ensures adherence to security standards
- **Breaking Change Detection**: Identifies API/interface changes

### Developer Agent
- **Code Generation**: Creates implementation based on requirements
- **Refactoring**: Improves existing code structure
- **Bug Fixing**: Analyzes and fixes identified issues
- **Optimization**: Enhances performance

### PM Agent (Project Manager)
- **Task Planning**: Breaks down requirements into tasks
- **Timeline Estimation**: Provides effort estimates
- **Resource Allocation**: Suggests team assignments
- **Progress Tracking**: Monitors development velocity

### PO Agent (Product Owner)
- **Requirement Analysis**: Clarifies and documents requirements
- **User Story Creation**: Generates acceptance criteria
- **Priority Management**: Ranks features by business value
- **Stakeholder Communication**: Prepares status reports

### QA Agent
- **Test Generation**: Creates unit and integration tests
- **Coverage Analysis**: Identifies untested code paths
- **Regression Detection**: Finds breaking changes
- **Performance Testing**: Identifies performance regressions

## Operational Modes

### Mode 1: Full Intelligence (Agent Server Running)

**Activation:**
```bash
./start_server.sh  # Starts agent server on port 2000
npm start          # Starts CLI with agent integration
```

**Capabilities:**
- All 7 agents available
- Real-time code analysis
- Intelligent recommendations
- Multi-agent workflows
- Continuous validation
- Performance profiling

**Example Workflow:**
```
User: "Create a REST API for user management"
1. Scout: Checks for existing user APIs (finds 85% match)
2. Architect: Suggests RESTful design with JWT auth
3. Guardian: Validates security requirements
4. Developer: Generates code with best practices
5. QA: Creates comprehensive test suite
6. Guardian: Continuous monitoring during development
```

### Mode 2: Basic Operations (Agent Server Not Running)

**Activation:**
```bash
npm start  # CLI only, no agent server
```

**Limitations:**
- Basic file operations only
- No intelligent analysis
- No duplication detection
- No security validation
- No architectural guidance
- Single-threaded operation

**Fallback Behavior:**
- CLI detects server unavailability
- Switches to basic mode automatically
- Warns user about reduced capabilities
- Continues with limited functionality

## Performance Characteristics

### With Agent Server

**Advantages:**
- Parallel agent execution (multi-threading)
- Background indexing and caching
- Incremental analysis updates
- Non-blocking UI operations

**Performance Metrics:**
- Agent response time: < 1s (simple queries)
- Code indexing: 1000 files/minute
- Duplication check: < 500ms (average)
- Security scan: 100ms/file
- Multi-agent workflow: 2-5s (typical)

### Without Agent Server

**Limitations:**
- Sequential operations only
- No background processing
- No caching mechanisms
- UI may block during operations

## Deployment Considerations

### Development Environment

```bash
# Start both components
./start_server.sh  # Terminal 1
npm start          # Terminal 2
```

### Production Deployment

**Option 1: Single Machine**
```yaml
# docker-compose.yml
services:
  agent-server:
    image: gemini-agent-server
    ports:
      - "2000:2000"
    environment:
      - GEMINI_ENV=production
  
  cli:
    image: gemini-cli
    depends_on:
      - agent-server
    environment:
      - AGENT_SERVER_URL=http://agent-server:2000
```

**Option 2: Distributed**
```yaml
# Agent Server on dedicated compute
# CLI on user machines pointing to remote server
AGENT_SERVER_URL=https://agent-server.company.com
```

### Scaling Considerations

**Horizontal Scaling:**
- Agent server can be load-balanced
- Stateless design allows multiple instances
- WebSocket connections use sticky sessions

**Resource Requirements:**
- Agent Server: 2 CPU cores, 4GB RAM minimum
- CLI: 1 CPU core, 2GB RAM minimum
- Database (if using): PostgreSQL/Redis for caching

## Security Considerations

### Communication Security
- TLS/SSL for production deployments
- API key authentication
- JWT tokens for session management
- Rate limiting on endpoints

### Code Analysis Security
- Sandboxed execution environment
- No execution of analyzed code
- Sanitized AST parsing
- Secure temp file handling

## Monitoring and Observability

### Health Checks
```bash
curl http://localhost:2000/health
# Returns: {"status": "healthy", "agents": 7, "uptime": 3600}
```

### Metrics Endpoints
```bash
curl http://localhost:2000/api/v1/metrics
# Returns agent performance metrics, request counts, error rates
```

### Logging
- Structured JSON logging
- Log levels: DEBUG, INFO, WARNING, ERROR
- Correlation IDs for request tracking
- Agent-specific log streams

## Troubleshooting

### Common Issues

**Issue: "Cannot connect to agent server"**
- Check if server is running: `ps aux | grep agent_server`
- Verify port availability: `lsof -i :2000`
- Check firewall settings

**Issue: "Agent timeout errors"**
- Increase timeout settings in CLI config
- Check server resource utilization
- Review agent server logs

**Issue: "Reduced functionality warning"**
- Agent server not running
- Start with: `./start_server.sh`
- Check Python dependencies: `pip install -r requirements.txt`

## Future Enhancements

### Planned Features
1. **Distributed Agent Execution**: Agents on separate machines
2. **Plugin Architecture**: Custom agent development
3. **Cloud-native Deployment**: Kubernetes operators
4. **Enhanced ML Models**: Fine-tuned for specific domains
5. **Real-time Collaboration**: Multi-user support

### Performance Optimizations
1. **GPU Acceleration**: For ML operations
2. **Incremental Analysis**: Faster re-analysis
3. **Distributed Caching**: Redis cluster
4. **Edge Deployment**: Local agent instances

## Conclusion

The dual-process architecture of Gemini Enterprise Architect provides a robust, scalable, and intelligent development assistance platform. The separation between the CLI and Agent Server allows for:

1. **Optimal Language Usage**: TypeScript for UI, Python for AI/ML
2. **Independent Scaling**: Scale components based on load
3. **Graceful Degradation**: Basic functionality without agents
4. **Enhanced Performance**: Parallel processing and caching
5. **Flexibility**: Deploy locally or distributed

This architecture ensures that developers get intelligent assistance when available while maintaining core functionality even in limited environments.