# Gemini CLI Enterprise Architect API Documentation

## Overview

The Gemini CLI Enterprise Architect API provides a comprehensive set of endpoints for enterprise-grade AI assistance, security scanning, monitoring, and authentication. This document serves as a complete reference for developers integrating with the API.

## Base URL

```
Production: https://api.yourcompany.com
Staging:    https://staging-api.yourcompany.com  
Development: http://localhost:8000
```

## Authentication

The API supports multiple authentication methods:

### 1. JWT Bearer Tokens
```http
Authorization: Bearer <jwt_token>
```

Get tokens via the `/api/v1/auth/token` endpoint:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_email@example.com&password=your_password"
```

### 2. API Keys
```http
X-API-Key: <api_key>
```

Create API keys via the `/api/v1/auth/api-keys` endpoint after authenticating with JWT.

### 3. OAuth2
Supports Google OAuth2 flow via `/api/v1/auth/oauth2/google/start`.

## Core Features

### 🤖 AI Agent System
- Advanced conversational AI with context memory
- Multiple specialized agents (analyst, architect, developer, etc.)
- Real-time streaming responses via WebSocket
- Scout-First architecture for code analysis

### 🔐 Security & Compliance
- Comprehensive vulnerability scanning
- Dependency analysis and CVE detection
- Secret scanning and policy enforcement
- Compliance reporting (OWASP, NIST, ISO27001)

### 📊 Monitoring & Analytics
- DORA metrics tracking
- Performance monitoring and alerting
- Real-time dashboards
- OpenTelemetry tracing

### 📚 Knowledge Management
- RAG-powered document search
- Vector similarity search
- Multi-source knowledge integration
- Context-aware responses

## API Endpoints

### Authentication Endpoints

#### POST /api/v1/auth/login
Authenticate with username/password.

**Request:**
```json
{
  "username": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "user_123",
    "username": "john_doe",
    "email": "user@example.com",
    "role": "user",
    "permissions": ["read", "write"]
  }
}
```

#### GET /api/v1/auth/me
Get current user information.

**Headers:**
```http
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": "user_123",
  "username": "john_doe",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "user",
  "permissions": ["read", "write"],
  "is_active": true,
  "created_at": "2024-01-01T12:00:00Z",
  "last_login": "2024-01-15T08:30:00Z"
}
```

### AI Agent Endpoints

#### POST /api/v1/agent/request
Send a request to an AI agent.

**Request:**
```json
{
  "type": "architect",
  "action": "design_system",
  "payload": {
    "requirements": "Design a microservices architecture for e-commerce",
    "constraints": ["cloud-native", "scalable", "secure"]
  },
  "context": {
    "project_type": "ecommerce",
    "team_size": "medium"
  },
  "timeout": 60
}
```

**Response:**
```json
{
  "id": "req_123",
  "success": true,
  "result": {
    "architecture": "...",
    "components": [...],
    "recommendations": [...]
  },
  "metadata": {
    "agent": "architect",
    "action": "design_system",
    "response_time": 2.5,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

#### WebSocket /ws/agent/stream
Real-time streaming responses from agents.

**Connect:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/agent/stream');

ws.onopen = function() {
  // Initialize connection
  ws.send(JSON.stringify({
    type: 'init'
  }));
};

// Send streaming request
ws.send(JSON.stringify({
  type: 'stream_request',
  request: {
    type: 'developer',
    action: 'code_review',
    payload: { code: "function example() { ... }" }
  }
}));
```

### Security Scanning Endpoints

#### POST /api/v1/security/scan
Start a comprehensive security scan.

**Request:**
```json
{
  "target": "/path/to/project",
  "scan_types": ["dependencies", "code", "secrets", "docker"]
}
```

**Response:**
```json
{
  "success": true,
  "timestamp": "2024-01-01T12:00:00Z",
  "scan_id": "scan_123",
  "target": "/path/to/project",
  "findings": [
    {
      "id": "sec_456",
      "severity": "high",
      "category": "dependency",
      "title": "Vulnerable dependency: requests",
      "description": "The requests library has a known vulnerability",
      "file_path": "requirements.txt",
      "line_number": 5,
      "recommendation": "Update requests to version 2.28.0 or higher"
    }
  ],
  "summary": {
    "critical": 0,
    "high": 1,
    "medium": 3,
    "low": 5,
    "info": 2
  },
  "risk_score": 35,
  "recommendations": [
    "Update vulnerable dependencies",
    "Fix high-severity code issues"
  ],
  "scan_duration": 45.2
}
```

#### GET /api/v1/security/compliance/report
Get compliance report for security frameworks.

**Parameters:**
- `framework`: owasp, nist, iso27001, pci_dss

**Response:**
```json
{
  "framework": "owasp",
  "timestamp": "2024-01-01T12:00:00Z",
  "overall_score": 75,
  "compliance_level": "Partially Compliant",
  "categories": [
    {
      "name": "Authentication",
      "score": 85,
      "status": "Compliant",
      "findings": 2,
      "recommendations": ["Implement MFA", "Review password policies"]
    }
  ],
  "action_items": [
    "Address critical security findings",
    "Implement missing security controls"
  ]
}
```

### Monitoring Endpoints

#### GET /api/v1/monitoring/dora
Get DORA metrics.

**Parameters:**
- `days`: Number of days to analyze (default: 30)

**Response:**
```json
{
  "deployment_frequency": 2.5,
  "lead_time_for_changes": 4.2,
  "mean_time_to_recovery": 1.5,
  "change_failure_rate": 5.0
}
```

#### GET /api/v1/monitoring/performance
Get current performance metrics.

**Response:**
```json
{
  "response_time_p50": 125.5,
  "response_time_p95": 450.0,
  "response_time_p99": 850.0,
  "requests_per_second": 150.0,
  "error_rate": 0.5,
  "cpu_usage": 45.0,
  "memory_usage": 60.0
}
```

#### GET /api/v1/monitoring/dashboard/summary
Get dashboard summary with key metrics.

**Response:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "dora_metrics": {
    "deployment_frequency": 2.5,
    "lead_time_for_changes": 4.2,
    "mean_time_to_recovery": 1.5,
    "change_failure_rate": 5.0
  },
  "performance_metrics": {
    "response_time_p95": 450.0,
    "requests_per_second": 150.0,
    "error_rate": 0.5,
    "cpu_usage": 45.0,
    "memory_usage": 60.0
  },
  "system_status": "healthy"
}
```

### Document Search Endpoints

#### POST /api/v1/rag/search
Search documents using vector similarity.

**Request:**
```json
{
  "query": "authentication implementation",
  "filters": {
    "file_type": "python",
    "tags": ["security"]
  },
  "limit": 5
}
```

**Response:**
```json
{
  "success": true,
  "timestamp": "2024-01-01T12:00:00Z",
  "results": [
    {
      "document": {
        "id": "doc_123",
        "title": "Authentication Guide",
        "content": "This guide covers authentication...",
        "metadata": {
          "file_name": "auth_guide.md",
          "file_type": "markdown",
          "tags": ["security", "authentication"]
        }
      },
      "score": 0.95,
      "highlights": ["authentication implementation", "JWT tokens"]
    }
  ],
  "total": 1,
  "query": "authentication implementation"
}
```

## Error Handling

### Standard Error Response Format

```json
{
  "error": {
    "code": 400,
    "message": "Bad request",
    "timestamp": "2024-01-01T12:00:00Z",
    "path": "/api/v1/endpoint"
  }
}
```

### Common HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `429` - Too Many Requests (rate limited)
- `500` - Internal Server Error

### Rate Limiting

- **Default Limits**: 1000 requests per minute per user
- **Rate Limit Headers**:
  ```http
  X-RateLimit-Limit: 1000
  X-RateLimit-Remaining: 999
  X-RateLimit-Reset: 1705394400
  ```
- **429 Response**: Includes `Retry-After` header

## OpenAPI Schema

The complete OpenAPI 3.0 schema is available at:
- Interactive docs: `/docs`
- ReDoc: `/redoc`  
- JSON schema: `/openapi.json`

## Security Features

### Request Security
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF tokens for web forms

### Headers
All responses include security headers:
```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

### Monitoring
- Request logging with correlation IDs
- Performance metrics via Prometheus
- Distributed tracing with OpenTelemetry
- Anomaly detection and alerting

## SDK Examples

### Python SDK Usage

```python
from gemini_client import GeminiAPI

# Initialize client
client = GeminiAPI(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# Agent request
response = await client.agent.request(
    agent_type="architect",
    action="design_system",
    payload={"requirements": "Design microservices architecture"}
)

# Security scan
scan_result = await client.security.scan(
    target="/path/to/project",
    scan_types=["dependencies", "code", "secrets"]
)

# Document search
search_results = await client.rag.search(
    query="authentication patterns",
    limit=10
)
```

### JavaScript SDK Usage

```javascript
import { GeminiAPI } from '@gemini/api-client';

const client = new GeminiAPI({
  baseURL: 'http://localhost:8000',
  apiKey: 'your-api-key'
});

// Agent request
const response = await client.agent.request({
  type: 'developer',
  action: 'code_review',
  payload: { code: 'function example() { ... }' }
});

// WebSocket streaming
const ws = client.agent.stream();
ws.on('message', (data) => {
  console.log('Streaming response:', data);
});

ws.send({
  type: 'developer',
  action: 'generate_tests',
  payload: { file_path: 'src/utils.py' }
});
```

## Environment Configuration

### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/db

# Redis
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET_KEY=your-secret-key
OAUTH2_GOOGLE_CLIENT_ID=your-google-client-id
OAUTH2_GOOGLE_CLIENT_SECRET=your-google-client-secret

# Security
SECURITY_SCAN_ENABLED=true
VULNERABILITY_DB_URL=https://vulnerability-db.com

# Monitoring
PROMETHEUS_ENABLED=true
OPENTELEMETRY_ENDPOINT=http://localhost:4317
DORA_METRICS_ENABLED=true

# Rate Limiting
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=INFO
STRUCTURED_LOGGING=true
```

### Optional Configuration

```bash
# Performance
CACHE_TTL=300
MAX_REQUEST_SIZE=10485760  # 10MB
TIMEOUT_SECONDS=30

# Features
AGENT_STREAMING=true
RAG_ENABLED=true
SCOUT_INDEXING=true

# Development
DEBUG=false
RELOAD=false
WORKERS=4
```

## Support

- **Documentation**: `/docs` (interactive API docs)
- **Health Check**: `/health` (system status)
- **Metrics**: `/metrics` (Prometheus metrics)
- **Issues**: GitHub repository issues
- **Email**: support@yourcompany.com

## Changelog

### v1.0.0 (2024-01-15)
- Initial API release
- Authentication system with JWT and OAuth2
- AI agent endpoints with streaming support
- Security scanning capabilities
- DORA metrics and performance monitoring
- RAG-powered document search
- Comprehensive OpenAPI documentation