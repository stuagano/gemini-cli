# API Specification

## Overview
This document defines the API contracts for the Gemini Enterprise Architect system, including REST endpoints, WebSocket protocols, and integration interfaces.

## Base Configuration
- **Base URL**: `https://api.gemini-architect.dev`
- **API Version**: `v1`
- **Authentication**: Bearer token (JWT)
- **Content-Type**: `application/json`
- **Rate Limiting**: 1000 requests/minute per user

## REST API Endpoints

### Authentication

#### POST /auth/login
**Description**: Authenticate user and receive access token

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 3600,
  "user": {
    "id": "user-123",
    "email": "user@example.com",
    "role": "developer"
  }
}
```

### BMAD Validation

#### POST /api/v1/bmad/validate
**Description**: Validate project documentation against BMAD requirements

**Request Body**:
```json
{
  "workspace_path": "/path/to/project",
  "validation_type": "full",
  "custom_requirements": {}
}
```

**Response** (200 OK):
```json
{
  "validation_id": "val-456",
  "is_valid": false,
  "score": 75,
  "errors": [
    {
      "type": "missing_section",
      "file": "PRD.md",
      "section": "Success Metrics",
      "severity": "major",
      "message": "Required section missing"
    }
  ],
  "warnings": [],
  "missing": ["business-case.md"],
  "recommendations": ["Add quantified success metrics"]
}
```

#### GET /api/v1/bmad/templates
**Description**: Get BMAD document templates

**Response** (200 OK):
```json
{
  "templates": [
    {
      "name": "business-case",
      "filename": "business-case.md",
      "content": "# Business Case Template\n..."
    },
    {
      "name": "prd",
      "filename": "PRD.md",
      "content": "# Product Requirements Document\n..."
    }
  ]
}
```

### AI Agents

#### POST /api/v1/agents/query
**Description**: Send query to AI agent

**Request Body**:
```json
{
  "agent": "scout",
  "query": "Find duplicate implementations of user authentication",
  "context": {
    "workspace": "/project",
    "files": ["src/**/*.ts"]
  },
  "options": {
    "max_results": 10,
    "include_suggestions": true
  }
}
```

**Response** (200 OK):
```json
{
  "request_id": "req-789",
  "agent": "scout",
  "status": "completed",
  "results": {
    "duplicates_found": 3,
    "locations": [
      {
        "file": "src/auth/login.ts",
        "line": 45,
        "similarity": 0.92
      }
    ],
    "suggestions": ["Consider extracting common auth logic to shared module"]
  },
  "processing_time": 1.23
}
```

#### GET /api/v1/agents/list
**Description**: Get available AI agents and their capabilities

**Response** (200 OK):
```json
{
  "agents": [
    {
      "id": "scout",
      "name": "Scout",
      "description": "Code analysis and duplicate detection",
      "capabilities": ["duplicate_detection", "code_analysis", "dependency_mapping"],
      "status": "online"
    },
    {
      "id": "architect",
      "name": "The Architect",
      "description": "System design and architecture guidance",
      "capabilities": ["design_review", "pattern_suggestion", "scalability_analysis"],
      "status": "online"
    }
  ]
}
```

### Cloud Pricing

#### GET /api/v1/pricing/estimate
**Description**: Get cloud cost estimates for current configuration

**Query Parameters**:
- `project_id`: Project identifier
- `environment`: development|staging|production
- `duration`: Projection duration in months

**Response** (200 OK):
```json
{
  "estimate_id": "est-234",
  "project_id": "proj-567",
  "monthly_cost": {
    "compute": 2500,
    "storage": 450,
    "network": 320,
    "total": 3270
  },
  "projections": {
    "3_months": 9810,
    "6_months": 19620,
    "12_months": 39240
  },
  "optimization_opportunities": [
    {
      "type": "reserved_instances",
      "potential_savings": 850,
      "recommendation": "Switch to 1-year reserved instances"
    }
  ],
  "currency": "USD",
  "last_updated": "2025-08-20T10:30:00Z"
}
```

### Project Management

#### GET /api/v1/epics
**Description**: Get project epics

**Response** (200 OK):
```json
{
  "epics": [
    {
      "id": "epic-001",
      "title": "VS Code Extension Development",
      "status": "in_progress",
      "stories": ["story-001", "story-002", "story-003"],
      "progress": 65,
      "priority": "high"
    }
  ]
}
```

#### GET /api/v1/stories/{story_id}
**Description**: Get story details

**Response** (200 OK):
```json
{
  "id": "story-001",
  "title": "Implement Tree Data Providers",
  "epic_id": "epic-001",
  "status": "completed",
  "acceptance_criteria": [...],
  "story_points": 5,
  "assignee": "dev-team"
}
```

## WebSocket API

### Connection
**Endpoint**: `wss://api.gemini-architect.dev/ws`

### Message Format
```json
{
  "type": "request|response|event",
  "id": "unique-message-id",
  "action": "action-name",
  "payload": {},
  "timestamp": "2025-08-20T10:30:00Z"
}
```

### Subscription Events

#### BMAD Status Updates
```json
{
  "type": "event",
  "action": "bmad.status.update",
  "payload": {
    "validation_id": "val-456",
    "score": 85,
    "is_valid": true,
    "changes": ["PRD.md updated"]
  }
}
```

#### Agent Response Streaming
```json
{
  "type": "response",
  "action": "agent.stream",
  "payload": {
    "request_id": "req-789",
    "chunk": "Based on my analysis...",
    "is_final": false
  }
}
```

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "workspace_path",
      "reason": "Path does not exist"
    },
    "request_id": "req-123",
    "timestamp": "2025-08-20T10:30:00Z"
  }
}
```

### Error Codes
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error
- `503` - Service Unavailable

## Rate Limiting

### Headers
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Window reset timestamp

### Throttling Response (429)
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "retry_after": 60
  }
}
```

## Pagination

### Request Parameters
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)
- `sort`: Sort field
- `order`: asc|desc

### Response Format
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

## Versioning

### URL Versioning
- Current: `/api/v1/`
- Legacy: `/api/v0/` (deprecated)

### Header Versioning
```
X-API-Version: 1.0
```

## Security

### Authentication
- Bearer token in Authorization header
- Token expiration: 1 hour
- Refresh token expiration: 30 days

### CORS Policy
```
Access-Control-Allow-Origin: https://app.gemini-architect.dev
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

### Data Encryption
- All endpoints require HTTPS
- Sensitive data encrypted at rest
- PII data masked in logs

---
*API Version*: 1.0
*Last Updated*: 2025-08-20
*OpenAPI Spec*: `/api/v1/openapi.json`