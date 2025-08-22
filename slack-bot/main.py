"""
Main application entry point for Gemini Enterprise Architect Slack Bot
Integrates all components and starts the FastAPI application
"""

import os
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slack_sdk.web.async_client import AsyncWebClient

# Import our modules
from .app import app as slack_app, agent_client, config, handler
from .commands import register_commands
from .interactive import register_interactive_components
from .notifications import notification_service
from .management import router as management_router
from .oauth import oauth_manager
from .middleware import (
    rate_limiter, error_handler, RateLimitConfig, 
    RequestValidationMiddleware, DEFAULT_RATE_LIMIT_CONFIG
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/slack-bot.log') if os.path.exists('logs') else logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration from environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENABLE_REDIS = os.getenv("ENABLE_REDIS", "false").lower() == "true"
REDIS_URL = os.getenv("REDIS_URL")

# Update rate limiting configuration
if ENABLE_REDIS and REDIS_URL:
    rate_limit_config = RateLimitConfig(
        requests_per_minute=100,
        requests_per_hour=2000,
        burst_size=20,
        enable_redis=True,
        redis_url=REDIS_URL
    )
    rate_limiter.config = rate_limit_config
    rate_limiter.limiter = rate_limiter.__class__(rate_limit_config).limiter

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Gemini Slack Bot...")
    
    try:
        # Initialize rate limiter
        await rate_limiter.initialize()
        
        # Initialize agent client
        await agent_client.__aenter__()
        
        # Initialize notification service
        slack_client = AsyncWebClient(token=config.bot_token)
        await notification_service.initialize(slack_client)
        
        # Start webhook server for notifications
        webhook_port = int(os.getenv("WEBHOOK_PORT", "3001"))
        await notification_service.start_webhook_server(webhook_port)
        
        # Register Slack event handlers
        register_commands(slack_app)
        register_interactive_components(slack_app)
        
        logger.info(f"Gemini Slack Bot started successfully in {ENVIRONMENT} mode")
        logger.info(f"Agent server URL: {config.agent_server_url}")
        logger.info(f"Webhook server running on port {webhook_port}")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    finally:
        # Cleanup
        logger.info("Shutting down Gemini Slack Bot...")
        await agent_client.__aexit__(None, None, None)
        logger.info("Gemini Slack Bot stopped")

# Create FastAPI app
app = FastAPI(
    title="Gemini Enterprise Architect Slack Bot",
    description="AI Agent integration for Slack workspaces",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if ENVIRONMENT == "development" else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if ENVIRONMENT == "development" else ["https://*.slack.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add custom middleware
app.middleware("http")(rate_limiter)
app.middleware("http")(error_handler)

# Add request validation middleware for Slack endpoints
if config.signing_secret:
    validation_middleware = RequestValidationMiddleware(config.signing_secret)
    app.middleware("http")(validation_middleware)

# Include routers
app.include_router(management_router)

# Slack event handling
@app.post("/slack/events")
async def slack_events(request: Request):
    """Handle Slack events"""
    try:
        return await handler.handle(request)
    except Exception as e:
        logger.error(f"Error handling Slack event: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to process Slack event"}
        )

@app.get("/slack/install")
async def slack_install():
    """Get Slack installation URL"""
    try:
        install_url = oauth_manager.get_authorization_url()
        return {
            "install_url": install_url,
            "message": "Click the URL to install the Gemini bot to your Slack workspace"
        }
    except Exception as e:
        logger.error(f"Error generating install URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate installation URL")

# Health check endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Gemini Enterprise Architect Slack Bot",
        "version": "1.0.0",
        "status": "running",
        "environment": ENVIRONMENT,
        "documentation": "/docs" if ENVIRONMENT == "development" else None
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check agent server connectivity
        agent_health = await agent_client.get_health()
        
        # Check notification service
        notification_status = "healthy" if notification_service.webhook_server_running else "degraded"
        
        # Check installed teams
        installations = oauth_manager.list_installations()
        
        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",  # This would be actual timestamp
            "services": {
                "agent_server": agent_health.get("status", "unknown"),
                "notification_service": notification_status,
                "rate_limiter": "healthy",
                "oauth_manager": "healthy"
            },
            "stats": {
                "installed_teams": len(installations),
                "environment": ENVIRONMENT,
                "redis_enabled": ENABLE_REDIS
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    try:
        installations = oauth_manager.list_installations()
        
        # Basic metrics (in production, this would be proper Prometheus format)
        metrics_data = {
            "slack_bot_installed_teams_total": len(installations),
            "slack_bot_active_channels_total": sum(len(inst.channel_subscriptions) for inst in installations),
            "slack_bot_active_users_total": sum(len(inst.user_preferences) for inst in installations),
            "slack_bot_notification_service_status": 1 if notification_service.webhook_server_running else 0,
            "slack_bot_uptime_seconds": 0  # Would track actual uptime
        }
        
        return metrics_data
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return JSONResponse(status_code=500, content={"error": "Metrics unavailable"})

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "NOT_FOUND",
                "message": "Endpoint not found",
                "path": str(request.url.path)
            }
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
    )

# Development utilities
if ENVIRONMENT == "development":
    @app.get("/debug/config")
    async def debug_config():
        """Debug endpoint to view configuration"""
        return {
            "environment": ENVIRONMENT,
            "log_level": LOG_LEVEL,
            "agent_server_url": config.agent_server_url,
            "redis_enabled": ENABLE_REDIS,
            "redis_url": REDIS_URL[:20] + "..." if REDIS_URL else None,
            "rate_limits": {
                "requests_per_minute": rate_limiter.config.requests_per_minute,
                "requests_per_hour": rate_limiter.config.requests_per_hour
            }
        }
    
    @app.get("/debug/teams")
    async def debug_teams():
        """Debug endpoint to view installed teams"""
        installations = oauth_manager.list_installations()
        return {
            "teams": [
                {
                    "team_id": inst.team_id,
                    "team_name": inst.team_name,
                    "installed_at": inst.installed_at.isoformat(),
                    "features": inst.enabled_features,
                    "channels": len(inst.channel_subscriptions),
                    "users": len(inst.user_preferences)
                }
                for inst in installations
            ]
        }

if __name__ == "__main__":
    import uvicorn
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, LOG_LEVEL.upper()))
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3000,
        reload=ENVIRONMENT == "development",
        log_level=LOG_LEVEL.lower(),
        workers=1 if ENVIRONMENT == "development" else 4
    )