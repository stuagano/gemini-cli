"""
Error Handling and Rate Limiting Middleware for Gemini Slack Bot
Provides comprehensive error handling, rate limiting, and request validation
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from slack_sdk.errors import SlackApiError
import aioredis

logger = logging.getLogger(__name__)

class ErrorCode(Enum):
    """Error codes for standardized error responses"""
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INVALID_REQUEST = "INVALID_REQUEST"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    AGENT_UNAVAILABLE = "AGENT_UNAVAILABLE"
    SLACK_API_ERROR = "SLACK_API_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10
    window_size: int = 60  # seconds
    enable_redis: bool = False
    redis_url: Optional[str] = None

@dataclass
class ErrorResponse:
    """Standardized error response structure"""
    error_code: str
    message: str
    details: Dict[str, Any]
    timestamp: str
    request_id: Optional[str] = None
    retry_after: Optional[int] = None
    
    def to_dict(self):
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
                "timestamp": self.timestamp,
                "request_id": self.request_id,
                "retry_after": self.retry_after
            }
        }

class InMemoryRateLimiter:
    """In-memory rate limiter for development and small deployments"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.request_counts: Dict[str, deque] = defaultdict(lambda: deque())
        self.hourly_counts: Dict[str, int] = defaultdict(int)
        self.hourly_reset: Dict[str, datetime] = {}
        
    def is_allowed(self, identifier: str) -> tuple[bool, Optional[int]]:
        """Check if request is allowed, return (allowed, retry_after_seconds)"""
        now = time.time()
        current_minute = int(now // 60)
        
        # Clean old entries
        minute_key = f"{identifier}:{current_minute}"
        requests_this_minute = self.request_counts[minute_key]
        
        # Remove entries older than window
        while requests_this_minute and requests_this_minute[0] < now - self.config.window_size:
            requests_this_minute.popleft()
        
        # Check burst limit
        if len(requests_this_minute) >= self.config.burst_size:
            retry_after = int(requests_this_minute[0] + self.config.window_size - now)
            return False, max(retry_after, 1)
        
        # Check minute limit
        if len(requests_this_minute) >= self.config.requests_per_minute:
            retry_after = 60 - int(now % 60)
            return False, retry_after
        
        # Check hourly limit
        hour_key = f"{identifier}:hour"
        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        if hour_key in self.hourly_reset and self.hourly_reset[hour_key] < current_hour:
            self.hourly_counts[hour_key] = 0
            self.hourly_reset[hour_key] = current_hour + timedelta(hours=1)
        elif hour_key not in self.hourly_reset:
            self.hourly_reset[hour_key] = current_hour + timedelta(hours=1)
        
        if self.hourly_counts[hour_key] >= self.config.requests_per_hour:
            retry_after = int((self.hourly_reset[hour_key] - datetime.now()).total_seconds())
            return False, retry_after
        
        # Allow request
        requests_this_minute.append(now)
        self.hourly_counts[hour_key] += 1
        return True, None

class RedisRateLimiter:
    """Redis-based rate limiter for production deployments"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.redis: Optional[aioredis.Redis] = None
        
    async def initialize(self):
        """Initialize Redis connection"""
        if self.config.redis_url:
            self.redis = await aioredis.from_url(self.config.redis_url)
            logger.info("Redis rate limiter initialized")
    
    async def is_allowed(self, identifier: str) -> tuple[bool, Optional[int]]:
        """Check if request is allowed using Redis"""
        if not self.redis:
            logger.warning("Redis not available, falling back to no rate limiting")
            return True, None
        
        try:
            now = int(time.time())
            minute_key = f"rate_limit:{identifier}:minute:{now // 60}"
            hour_key = f"rate_limit:{identifier}:hour:{now // 3600}"
            
            # Use Redis pipeline for atomic operations
            pipe = self.redis.pipeline()
            
            # Check and increment minute counter
            pipe.get(minute_key)
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)
            
            # Check and increment hour counter
            pipe.get(hour_key)
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)
            
            results = await pipe.execute()
            
            minute_count = int(results[0]) if results[0] else 0
            hour_count = int(results[3]) if results[3] else 0
            
            # Check limits
            if minute_count >= self.config.requests_per_minute:
                retry_after = 60 - (now % 60)
                return False, retry_after
            
            if hour_count >= self.config.requests_per_hour:
                retry_after = 3600 - (now % 3600)
                return False, retry_after
            
            return True, None
            
        except Exception as e:
            logger.error(f"Redis rate limiter error: {e}")
            return True, None  # Fail open

class RateLimitMiddleware:
    """Rate limiting middleware"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        if config.enable_redis:
            self.limiter = RedisRateLimiter(config)
        else:
            self.limiter = InMemoryRateLimiter(config)
    
    async def initialize(self):
        """Initialize rate limiter"""
        if isinstance(self.limiter, RedisRateLimiter):
            await self.limiter.initialize()
    
    def get_identifier(self, request: Request) -> str:
        """Get rate limit identifier from request"""
        # Try to get team_id from various sources
        team_id = None
        
        # From path parameters
        if hasattr(request, 'path_params') and 'team_id' in request.path_params:
            team_id = request.path_params['team_id']
        
        # From Slack headers
        if not team_id:
            team_id = request.headers.get('X-Slack-Team-Id')
        
        # From request body (for Slack events)
        if not team_id and hasattr(request, '_body'):
            try:
                body = json.loads(request._body)
                if 'team' in body:
                    team_id = body['team'].get('id')
                elif 'team_id' in body:
                    team_id = body['team_id']
            except:
                pass
        
        # Fall back to IP address
        if not team_id:
            forwarded_for = request.headers.get('X-Forwarded-For')
            if forwarded_for:
                team_id = forwarded_for.split(',')[0].strip()
            else:
                team_id = request.client.host if request.client else 'unknown'
        
        return team_id
    
    async def __call__(self, request: Request, call_next):
        """Rate limiting middleware"""
        identifier = self.get_identifier(request)
        
        # Check rate limit
        if isinstance(self.limiter, InMemoryRateLimiter):
            allowed, retry_after = self.limiter.is_allowed(identifier)
        else:
            allowed, retry_after = await self.limiter.is_allowed(identifier)
        
        if not allowed:
            error_response = ErrorResponse(
                error_code=ErrorCode.RATE_LIMIT_EXCEEDED.value,
                message="Rate limit exceeded",
                details={
                    "identifier": identifier,
                    "retry_after": retry_after,
                    "limits": {
                        "requests_per_minute": self.config.requests_per_minute,
                        "requests_per_hour": self.config.requests_per_hour
                    }
                },
                timestamp=datetime.now().isoformat(),
                retry_after=retry_after
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=error_response.to_dict(),
                headers={"Retry-After": str(retry_after)} if retry_after else {}
            )
        
        return await call_next(request)

class ErrorHandlingMiddleware:
    """Global error handling middleware"""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.last_reset = datetime.now()
    
    async def __call__(self, request: Request, call_next):
        """Error handling middleware"""
        request_id = request.headers.get('X-Request-ID', f"req_{int(time.time())}")
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Log successful requests
            duration = time.time() - start_time
            if duration > 5.0:  # Log slow requests
                logger.warning(f"Slow request {request_id}: {duration:.2f}s - {request.method} {request.url}")
            
            return response
            
        except SlackApiError as e:
            logger.error(f"Slack API error in request {request_id}: {e}")
            
            error_response = ErrorResponse(
                error_code=ErrorCode.SLACK_API_ERROR.value,
                message=f"Slack API error: {e.response['error'] if e.response else str(e)}",
                details={
                    "slack_error": e.response['error'] if e.response else str(e),
                    "endpoint": str(request.url),
                    "method": request.method
                },
                timestamp=datetime.now().isoformat(),
                request_id=request_id
            )
            
            status_code = status.HTTP_400_BAD_REQUEST
            if 'rate_limited' in str(e).lower():
                status_code = status.HTTP_429_TOO_MANY_REQUESTS
                error_response.retry_after = 60
            elif 'not_found' in str(e).lower():
                status_code = status.HTTP_404_NOT_FOUND
            elif 'invalid_auth' in str(e).lower():
                status_code = status.HTTP_401_UNAUTHORIZED
            
            return JSONResponse(
                status_code=status_code,
                content=error_response.to_dict()
            )
            
        except HTTPException as e:
            logger.error(f"HTTP exception in request {request_id}: {e}")
            
            error_response = ErrorResponse(
                error_code=ErrorCode.INVALID_REQUEST.value,
                message=e.detail,
                details={
                    "status_code": e.status_code,
                    "endpoint": str(request.url)
                },
                timestamp=datetime.now().isoformat(),
                request_id=request_id
            )
            
            return JSONResponse(
                status_code=e.status_code,
                content=error_response.to_dict()
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout in request {request_id}")
            
            error_response = ErrorResponse(
                error_code=ErrorCode.TIMEOUT_ERROR.value,
                message="Request timed out",
                details={
                    "endpoint": str(request.url),
                    "duration": time.time() - start_time
                },
                timestamp=datetime.now().isoformat(),
                request_id=request_id
            )
            
            return JSONResponse(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                content=error_response.to_dict()
            )
            
        except Exception as e:
            logger.error(f"Unhandled exception in request {request_id}: {e}")
            self._track_error(type(e).__name__)
            
            error_response = ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR.value,
                message="An internal error occurred",
                details={
                    "error_type": type(e).__name__,
                    "endpoint": str(request.url),
                    "duration": time.time() - start_time
                },
                timestamp=datetime.now().isoformat(),
                request_id=request_id
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response.to_dict()
            )
    
    def _track_error(self, error_type: str):
        """Track error counts for monitoring"""
        # Reset counts hourly
        now = datetime.now()
        if now - self.last_reset > timedelta(hours=1):
            self.error_counts.clear()
            self.last_reset = now
        
        self.error_counts[error_type] += 1
        
        # Alert on high error rates
        if self.error_counts[error_type] > 10:
            logger.critical(f"High error rate detected: {error_type} - {self.error_counts[error_type]} errors in the last hour")

class RequestValidationMiddleware:
    """Request validation middleware for Slack requests"""
    
    def __init__(self, signing_secret: str):
        self.signing_secret = signing_secret
    
    async def __call__(self, request: Request, call_next):
        """Validate Slack requests"""
        # Skip validation for non-Slack endpoints
        if not request.url.path.startswith('/slack/'):
            return await call_next(request)
        
        # Validate Slack signature
        if not await self._verify_slack_signature(request):
            error_response = ErrorResponse(
                error_code=ErrorCode.AUTHENTICATION_FAILED.value,
                message="Invalid Slack signature",
                details={
                    "endpoint": str(request.url),
                    "headers": dict(request.headers)
                },
                timestamp=datetime.now().isoformat()
            )
            
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_response.to_dict()
            )
        
        return await call_next(request)
    
    async def _verify_slack_signature(self, request: Request) -> bool:
        """Verify Slack request signature"""
        import hmac
        import hashlib
        
        timestamp = request.headers.get("X-Slack-Request-Timestamp")
        signature = request.headers.get("X-Slack-Signature")
        
        if not timestamp or not signature:
            return False
        
        # Check timestamp (prevent replay attacks)
        if abs(time.time() - int(timestamp)) > 60 * 5:  # 5 minutes
            return False
        
        # Get request body
        body = await request.body()
        
        # Create signature
        sig_basestring = f"v0:{timestamp}:{body.decode()}"
        expected_signature = "v0=" + hmac.new(
            self.signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)

class CircuitBreaker:
    """Circuit breaker for external service calls"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable) -> Callable:
        """Decorator for circuit breaker"""
        async def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if time.time() - self.last_failure_time < self.recovery_timeout:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Service temporarily unavailable (circuit breaker open)"
                    )
                else:
                    self.state = "HALF_OPEN"
            
            try:
                result = await func(*args, **kwargs)
                
                # Success - reset circuit breaker
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    self.last_failure_time = None
                
                return result
                
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
                
                raise e
        
        return wrapper

def create_error_handler(error_code: ErrorCode) -> Callable:
    """Create standardized error handler"""
    def handler(request: Request, exc: Exception):
        error_response = ErrorResponse(
            error_code=error_code.value,
            message=str(exc),
            details={
                "error_type": type(exc).__name__,
                "endpoint": str(request.url)
            },
            timestamp=datetime.now().isoformat()
        )
        
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        if error_code == ErrorCode.RATE_LIMIT_EXCEEDED:
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        elif error_code == ErrorCode.INVALID_REQUEST:
            status_code = status.HTTP_400_BAD_REQUEST
        elif error_code == ErrorCode.AUTHENTICATION_FAILED:
            status_code = status.HTTP_401_UNAUTHORIZED
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.to_dict()
        )
    
    return handler

# Default configurations
DEFAULT_RATE_LIMIT_CONFIG = RateLimitConfig(
    requests_per_minute=60,
    requests_per_hour=1000,
    burst_size=10,
    enable_redis=False
)

# Global instances
rate_limiter = RateLimitMiddleware(DEFAULT_RATE_LIMIT_CONFIG)
error_handler = ErrorHandlingMiddleware()
circuit_breaker = CircuitBreaker()