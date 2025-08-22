"""
OpenAPI Schema Definitions
Detailed request/response models and examples for API documentation
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, EmailStr
from enum import Enum

# Base models
class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = Field(default=True, description="Request success status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
class ErrorResponse(BaseModel):
    """Error response model"""
    error: Dict[str, Any] = Field(description="Error details")
    
    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "code": 400,
                    "message": "Bad request",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "path": "/api/v1/endpoint"
                }
            }
        }

class PaginationMeta(BaseModel):
    """Pagination metadata"""
    page: int = Field(description="Current page number")
    per_page: int = Field(description="Items per page")
    total: int = Field(description="Total number of items")
    pages: int = Field(description="Total number of pages")

class PaginatedResponse(BaseResponse):
    """Paginated response base"""
    meta: PaginationMeta = Field(description="Pagination metadata")

# Authentication schemas
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    SECURITY_SCAN = "security_scan"
    METRICS_VIEW = "metrics_view"

class User(BaseModel):
    """User model"""
    id: str = Field(description="Unique user identifier")
    username: str = Field(description="Username")
    email: EmailStr = Field(description="User email address")
    full_name: Optional[str] = Field(None, description="Full name")
    role: UserRole = Field(description="User role")
    permissions: List[Permission] = Field(description="User permissions")
    is_active: bool = Field(default=True, description="Account active status")
    created_at: datetime = Field(description="Account creation date")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "user_123",
                "username": "john_doe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "role": "user",
                "permissions": ["read", "write"],
                "is_active": True,
                "created_at": "2024-01-01T12:00:00Z",
                "last_login": "2024-01-15T08:30:00Z"
            }
        }

class UserCreate(BaseModel):
    """User creation model"""
    username: str = Field(min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(description="User email address")
    password: str = Field(min_length=8, description="User password")
    full_name: Optional[str] = Field(None, description="Full name")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    
    class Config:
        schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "securepassword123",
                "full_name": "John Doe",
                "role": "user"
            }
        }

class LoginRequest(BaseModel):
    """Login request model"""
    username: str = Field(description="Username or email")
    password: str = Field(description="User password")
    
    class Config:
        schema_extra = {
            "example": {
                "username": "john@example.com",
                "password": "securepassword123"
            }
        }

class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token expiration time in seconds")
    user: User = Field(description="User information")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": "user_123",
                    "username": "john_doe",
                    "email": "john@example.com",
                    "role": "user"
                }
            }
        }

# AI Agent schemas
class ConversationMessage(BaseModel):
    """Conversation message model"""
    id: str = Field(description="Message ID")
    role: str = Field(description="Message role (user, assistant)")
    content: str = Field(description="Message content")
    timestamp: datetime = Field(description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "msg_123",
                "role": "user",
                "content": "Hello, can you help me with my code?",
                "timestamp": "2024-01-01T12:00:00Z",
                "metadata": {"file_context": "main.py"}
            }
        }

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "How can I optimize this Python function?",
                "conversation_id": "conv_123",
                "context": {
                    "file_name": "utils.py",
                    "line_number": 42
                }
            }
        }

class ChatResponse(BaseResponse):
    """Chat response model"""
    message: ConversationMessage = Field(description="Assistant response")
    conversation_id: str = Field(description="Conversation ID")
    usage: Optional[Dict[str, int]] = Field(None, description="Token usage statistics")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "timestamp": "2024-01-01T12:00:00Z",
                "message": {
                    "id": "msg_456",
                    "role": "assistant",
                    "content": "I can help you optimize that function. Here are some suggestions...",
                    "timestamp": "2024-01-01T12:00:00Z"
                },
                "conversation_id": "conv_123",
                "usage": {
                    "prompt_tokens": 150,
                    "completion_tokens": 75,
                    "total_tokens": 225
                }
            }
        }

# RAG schemas
class DocumentMetadata(BaseModel):
    """Document metadata model"""
    file_name: str = Field(description="Document file name")
    file_type: str = Field(description="Document file type")
    size: int = Field(description="Document size in bytes")
    created_at: datetime = Field(description="Document creation date")
    modified_at: datetime = Field(description="Document modification date")
    tags: List[str] = Field(default=[], description="Document tags")

class Document(BaseModel):
    """Document model"""
    id: str = Field(description="Document ID")
    title: str = Field(description="Document title")
    content: str = Field(description="Document content")
    metadata: DocumentMetadata = Field(description="Document metadata")
    embedding_id: Optional[str] = Field(None, description="Vector embedding ID")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "doc_123",
                "title": "API Documentation",
                "content": "This document describes the API endpoints...",
                "metadata": {
                    "file_name": "api_docs.md",
                    "file_type": "markdown",
                    "size": 1024,
                    "created_at": "2024-01-01T12:00:00Z",
                    "modified_at": "2024-01-01T12:00:00Z",
                    "tags": ["api", "documentation"]
                }
            }
        }

class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(description="Search query")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "authentication implementation",
                "filters": {
                    "file_type": "python",
                    "tags": ["security"]
                },
                "limit": 5
            }
        }

class SearchResult(BaseModel):
    """Search result model"""
    document: Document = Field(description="Found document")
    score: float = Field(description="Relevance score")
    highlights: List[str] = Field(description="Highlighted text excerpts")

class SearchResponse(BaseResponse):
    """Search response model"""
    results: List[SearchResult] = Field(description="Search results")
    total: int = Field(description="Total number of results")
    query: str = Field(description="Original search query")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "timestamp": "2024-01-01T12:00:00Z",
                "results": [
                    {
                        "document": {
                            "id": "doc_123",
                            "title": "Authentication Guide",
                            "content": "This guide covers authentication..."
                        },
                        "score": 0.95,
                        "highlights": ["authentication implementation", "JWT tokens"]
                    }
                ],
                "total": 1,
                "query": "authentication implementation"
            }
        }

# Security schemas
class SecuritySeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class SecurityFinding(BaseModel):
    """Security finding model"""
    id: str = Field(description="Finding ID")
    severity: SecuritySeverity = Field(description="Severity level")
    category: str = Field(description="Finding category")
    title: str = Field(description="Finding title")
    description: str = Field(description="Finding description")
    file_path: Optional[str] = Field(None, description="Affected file path")
    line_number: Optional[int] = Field(None, description="Affected line number")
    recommendation: str = Field(description="Recommended fix")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "sec_123",
                "severity": "high",
                "category": "dependency",
                "title": "Vulnerable dependency: requests",
                "description": "The requests library has a known vulnerability",
                "file_path": "requirements.txt",
                "line_number": 5,
                "recommendation": "Update requests to version 2.28.0 or higher"
            }
        }

class SecurityScanRequest(BaseModel):
    """Security scan request model"""
    target: str = Field(description="Scan target (file, directory, or repository)")
    scan_types: List[str] = Field(default=["dependencies", "code", "secrets"], description="Types of scans to run")
    
    class Config:
        schema_extra = {
            "example": {
                "target": "/path/to/project",
                "scan_types": ["dependencies", "code", "secrets", "docker"]
            }
        }

class SecurityReport(BaseResponse):
    """Security scan report model"""
    scan_id: str = Field(description="Scan ID")
    target: str = Field(description="Scan target")
    findings: List[SecurityFinding] = Field(description="Security findings")
    summary: Dict[str, int] = Field(description="Findings summary by severity")
    risk_score: int = Field(ge=0, le=100, description="Overall risk score (0-100)")
    recommendations: List[str] = Field(description="General recommendations")
    scan_duration: float = Field(description="Scan duration in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "timestamp": "2024-01-01T12:00:00Z",
                "scan_id": "scan_123",
                "target": "/path/to/project",
                "findings": [],
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
        }

# Monitoring schemas
class MetricDataPoint(BaseModel):
    """Metric data point model"""
    timestamp: datetime = Field(description="Data point timestamp")
    value: float = Field(description="Metric value")
    labels: Optional[Dict[str, str]] = Field(None, description="Metric labels")

class MetricSeries(BaseModel):
    """Metric time series model"""
    name: str = Field(description="Metric name")
    unit: str = Field(description="Metric unit")
    data_points: List[MetricDataPoint] = Field(description="Time series data")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "deployment_frequency",
                "unit": "deployments/day",
                "data_points": [
                    {
                        "timestamp": "2024-01-01T12:00:00Z",
                        "value": 2.5,
                        "labels": {"environment": "production"}
                    }
                ]
            }
        }

class DORAMetrics(BaseModel):
    """DORA metrics model"""
    deployment_frequency: float = Field(description="Deployments per day")
    lead_time_for_changes: float = Field(description="Lead time in hours")
    mean_time_to_recovery: float = Field(description="MTTR in hours")
    change_failure_rate: float = Field(description="Change failure rate as percentage")
    
    class Config:
        schema_extra = {
            "example": {
                "deployment_frequency": 2.5,
                "lead_time_for_changes": 4.2,
                "mean_time_to_recovery": 1.5,
                "change_failure_rate": 5.0
            }
        }

class PerformanceMetrics(BaseModel):
    """Performance metrics model"""
    response_time_p50: float = Field(description="50th percentile response time (ms)")
    response_time_p95: float = Field(description="95th percentile response time (ms)")
    response_time_p99: float = Field(description="99th percentile response time (ms)")
    requests_per_second: float = Field(description="Requests per second")
    error_rate: float = Field(description="Error rate as percentage")
    cpu_usage: float = Field(description="CPU usage percentage")
    memory_usage: float = Field(description="Memory usage percentage")
    
    class Config:
        schema_extra = {
            "example": {
                "response_time_p50": 125.5,
                "response_time_p95": 450.0,
                "response_time_p99": 850.0,
                "requests_per_second": 150.0,
                "error_rate": 0.5,
                "cpu_usage": 45.0,
                "memory_usage": 60.0
            }
        }

# API Key schemas
class APIKeyCreate(BaseModel):
    """API key creation model"""
    name: str = Field(description="API key name")
    permissions: List[Permission] = Field(description="API key permissions")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Production API Key",
                "permissions": ["read", "write"],
                "expires_at": "2024-12-31T23:59:59Z"
            }
        }

class APIKey(BaseModel):
    """API key model"""
    id: str = Field(description="API key ID")
    name: str = Field(description="API key name")
    key_prefix: str = Field(description="API key prefix (first 8 characters)")
    permissions: List[Permission] = Field(description="API key permissions")
    created_at: datetime = Field(description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    last_used: Optional[datetime] = Field(None, description="Last used timestamp")
    is_active: bool = Field(description="Active status")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "key_123",
                "name": "Production API Key",
                "key_prefix": "gek_abcd",
                "permissions": ["read", "write"],
                "created_at": "2024-01-01T12:00:00Z",
                "expires_at": "2024-12-31T23:59:59Z",
                "last_used": "2024-01-15T08:30:00Z",
                "is_active": True
            }
        }

# Webhook schemas
class WebhookEvent(str, Enum):
    SCAN_COMPLETED = "scan_completed"
    DEPLOYMENT_STARTED = "deployment_started"
    DEPLOYMENT_COMPLETED = "deployment_completed"
    DEPLOYMENT_FAILED = "deployment_failed"
    ALERT_TRIGGERED = "alert_triggered"

class WebhookPayload(BaseModel):
    """Webhook payload model"""
    event: WebhookEvent = Field(description="Event type")
    timestamp: datetime = Field(description="Event timestamp")
    data: Dict[str, Any] = Field(description="Event data")
    
    class Config:
        schema_extra = {
            "example": {
                "event": "scan_completed",
                "timestamp": "2024-01-01T12:00:00Z",
                "data": {
                    "scan_id": "scan_123",
                    "status": "completed",
                    "findings_count": 5
                }
            }
        }

# Common response schemas for documentation
class SuccessResponse(BaseResponse):
    """Generic success response"""
    message: str = Field(description="Success message")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "timestamp": "2024-01-01T12:00:00Z",
                "message": "Operation completed successfully"
            }
        }

class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    detail: List[Dict[str, Any]] = Field(description="Validation error details")
    
    class Config:
        schema_extra = {
            "example": {
                "detail": [
                    {
                        "loc": ["body", "email"],
                        "msg": "field required",
                        "type": "value_error.missing"
                    }
                ]
            }
        }