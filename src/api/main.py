"""
FastAPI Main Application
Complete API setup with documentation, security, and monitoring
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
import uvicorn

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# Import routers
from api.auth_routes import router as auth_router
from api.rag_endpoints import router as rag_router
from api.router import router as main_router
from api.monitoring_routes import router as monitoring_router
from api.security_routes import router as security_router

# Import security middleware
from security.middleware import setup_security_middleware
from security.auth import auth_manager

# Import monitoring
from monitoring.dora_metrics import DORAMetricsTracker
from monitoring.performance import performance_monitor

logger = logging.getLogger(__name__)

# Application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    # Startup
    logger.info("Starting Gemini CLI API...")
    
    # Initialize auth manager
    await auth_manager.initialize()
    
    # Initialize metrics tracker
    dora_tracker = DORAMetricsTracker()
    app.state.dora_tracker = dora_tracker
    
    # Initialize performance monitor
    app.state.performance_monitor = performance_monitor
    
    yield
    
    # Shutdown
    logger.info("Shutting down Gemini CLI API...")
    
    # Cleanup Redis connections
    if hasattr(auth_manager, 'redis_client'):
        await auth_manager.redis_client.close()

# Create FastAPI app
app = FastAPI(
    title="Gemini CLI Enterprise Architect",
    description="""
    ## Gemini CLI Enterprise Architect API
    
    A comprehensive enterprise-grade AI assistant with advanced capabilities:
    
    ### Features
    - 🔐 **Authentication & Authorization**: OAuth2, JWT, RBAC with role-based permissions
    - 🤖 **AI Agent System**: Advanced conversational AI with memory and context
    - 📚 **RAG (Retrieval Augmented Generation)**: Document search and knowledge base
    - 📊 **DORA Metrics**: DevOps Research and Assessment metrics tracking
    - 🔍 **Security Scanning**: Comprehensive vulnerability assessment
    - 📈 **Performance Monitoring**: Real-time metrics and optimization
    - ☁️ **Cloud Integration**: GCP Vertex AI and enterprise services
    
    ### Security
    - Rate limiting and DDoS protection
    - CSRF protection and security headers
    - Input validation and sanitization
    - API key management
    - Request logging and monitoring
    
    ### Authentication
    Use the `/api/v1/auth/token` endpoint to obtain access tokens.
    Include the token in the `Authorization` header: `Bearer <token>`
    
    ### Rate Limits
    - 1000 requests per minute per user
    - Higher limits available for enterprise accounts
    
    ### Support
    For support and documentation, visit: https://github.com/your-org/gemini-cli
    """,
    version="1.0.0",
    contact={
        "name": "Gemini CLI Support",
        "url": "https://github.com/your-org/gemini-cli",
        "email": "support@yourcompany.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    terms_of_service="https://yourcompany.com/terms",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User authentication, authorization, and account management"
        },
        {
            "name": "AI Agent",
            "description": "Conversational AI agent with advanced capabilities"
        },
        {
            "name": "RAG",
            "description": "Retrieval Augmented Generation for document search"
        },
        {
            "name": "Security",
            "description": "Security scanning and vulnerability assessment"
        },
        {
            "name": "Monitoring",
            "description": "Performance metrics and DORA tracking"
        },
        {
            "name": "Health",
            "description": "System health and status endpoints"
        }
    ],
    lifespan=lifespan
)

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        contact=app.contact,
        license_info=app.license_info,
        terms_of_service=app.terms_of_service
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token"
        },
        "APIKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "Enter your API key"
        },
        "OAuth2": {
            "type": "oauth2",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": "/api/v1/auth/oauth2/google/start",
                    "tokenUrl": "/api/v1/auth/token",
                    "scopes": {
                        "read": "Read access",
                        "write": "Write access",
                        "admin": "Administrative access"
                    }
                }
            }
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [
        {"BearerAuth": []},
        {"APIKeyAuth": []},
        {"OAuth2": ["read", "write"]}
    ]
    
    # Add servers
    openapi_schema["servers"] = [
        {
            "url": "https://api.yourcompany.com",
            "description": "Production server"
        },
        {
            "url": "https://staging-api.yourcompany.com", 
            "description": "Staging server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        }
    ]
    
    # Add example responses
    for path_item in openapi_schema["paths"].values():
        for operation in path_item.values():
            if isinstance(operation, dict) and "responses" in operation:
                # Add common error responses
                if "401" not in operation["responses"]:
                    operation["responses"]["401"] = {
                        "description": "Unauthorized",
                        "content": {
                            "application/json": {
                                "example": {"detail": "Could not validate credentials"}
                            }
                        }
                    }
                if "403" not in operation["responses"]:
                    operation["responses"]["403"] = {
                        "description": "Forbidden", 
                        "content": {
                            "application/json": {
                                "example": {"detail": "Not enough permissions"}
                            }
                        }
                    }
                if "429" not in operation["responses"]:
                    operation["responses"]["429"] = {
                        "description": "Too Many Requests",
                        "content": {
                            "application/json": {
                                "example": {"detail": "Rate limit exceeded"}
                            }
                        }
                    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Setup security middleware
setup_security_middleware(app)

# Include routers
app.include_router(auth_router)
app.include_router(rag_router)
app.include_router(main_router)
app.include_router(monitoring_router)
app.include_router(security_router)

# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": app.version,
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """Detailed system health check"""
    try:
        # Check Redis
        await auth_manager.redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if redis_status == "healthy" else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": app.version,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "services": {
            "redis": redis_status,
            "auth": "healthy",
            "api": "healthy"
        },
        "metrics": {
            "uptime": "unknown",  # Would track actual uptime
            "requests_per_minute": "unknown",  # Would track from metrics
            "error_rate": "unknown"  # Would track from metrics
        }
    }

@app.get("/", response_class=HTMLResponse, tags=["Health"])
async def root():
    """API documentation root"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gemini CLI Enterprise Architect API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .header { text-align: center; margin-bottom: 30px; }
            .links { display: flex; gap: 20px; justify-content: center; margin: 30px 0; }
            .link { padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
            .link:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 Gemini CLI Enterprise Architect API</h1>
            <p>Advanced AI Assistant with Enterprise Features</p>
        </div>
        
        <div class="links">
            <a href="/docs" class="link">📚 Interactive Documentation</a>
            <a href="/redoc" class="link">📖 ReDoc Documentation</a>
            <a href="/openapi.json" class="link">🔧 OpenAPI Schema</a>
            <a href="/health" class="link">💚 Health Check</a>
        </div>
        
        <div style="margin-top: 40px;">
            <h2>🔐 Authentication</h2>
            <p>Use <code>/api/v1/auth/token</code> to get access tokens</p>
            
            <h2>🤖 Features</h2>
            <ul>
                <li>AI Agent with conversational memory</li>
                <li>RAG-powered document search</li>
                <li>Security scanning and assessment</li>
                <li>DORA metrics tracking</li>
                <li>Performance monitoring</li>
                <li>OAuth2 and JWT authentication</li>
                <li>Role-based access control</li>
            </ul>
        </div>
    </body>
    </html>
    """)

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path)
            }
        },
        headers=exc.headers
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path)
            }
        }
    )

# Development server
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )