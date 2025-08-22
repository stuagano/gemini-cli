"""
Security middleware for FastAPI
Rate limiting, CORS, security headers, and request validation
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import hashlib
import hmac

from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import RequestResponseEndpoint
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for request validation and protection"""
    
    def __init__(
        self,
        app,
        redis_url: str = "redis://localhost:6379",
        rate_limit_requests: int = 1000,
        rate_limit_window: int = 60,
        enable_csrf: bool = True,
        max_request_size: int = 10 * 1024 * 1024,  # 10MB
        blocked_ips: List[str] = None
    ):
        super().__init__(app)
        self.redis_url = redis_url
        self.redis_client = None
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_window = rate_limit_window
        self.enable_csrf = enable_csrf
        self.max_request_size = max_request_size
        self.blocked_ips = set(blocked_ips or [])
        
        # Security headers
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Main middleware dispatcher"""
        start_time = time.time()
        
        try:
            # Initialize Redis client if needed
            if not self.redis_client:
                self.redis_client = redis.from_url(self.redis_url)
            
            # Security checks
            await self._check_blocked_ip(request)
            await self._check_request_size(request)
            await self._rate_limit_check(request)
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            self._add_security_headers(response)
            
            # Log request
            await self._log_request(request, response, time.time() - start_time)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def _check_blocked_ip(self, request: Request):
        """Check if IP is blocked"""
        client_ip = self._get_client_ip(request)
        
        if client_ip in self.blocked_ips:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="IP address blocked"
            )
        
        # Check dynamic blocked IPs in Redis
        if self.redis_client:
            is_blocked = await self.redis_client.exists(f"blocked_ip:{client_ip}")
            if is_blocked:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="IP address temporarily blocked"
                )
    
    async def _check_request_size(self, request: Request):
        """Check request size limit"""
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request too large"
            )
    
    async def _rate_limit_check(self, request: Request):
        """Rate limiting check"""
        if not self.redis_client:
            return
        
        client_ip = self._get_client_ip(request)
        user_id = getattr(request.state, 'user_id', None)
        
        # Create rate limit key (prefer user ID over IP)
        rate_key = f"rate_limit:{user_id or client_ip}"
        
        # Check current request count
        current_requests = await self.redis_client.get(rate_key)
        
        if current_requests and int(current_requests) >= self.rate_limit_requests:
            # Get TTL to include in response
            ttl = await self.redis_client.ttl(rate_key)
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "Retry-After": str(ttl),
                    "X-RateLimit-Limit": str(self.rate_limit_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + ttl)
                }
            )
        
        # Increment request count
        pipe = self.redis_client.pipeline()
        pipe.incr(rate_key)
        pipe.expire(rate_key, self.rate_limit_window)
        await pipe.execute()
        
        # Add rate limit headers to request state for response
        remaining = max(0, self.rate_limit_requests - int(current_requests or 0) - 1)
        request.state.rate_limit_headers = {
            "X-RateLimit-Limit": str(self.rate_limit_requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(time.time()) + self.rate_limit_window)
        }
    
    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        # Add rate limit headers if available
        if hasattr(response, 'state') and hasattr(response.state, 'rate_limit_headers'):
            for header, value in response.state.rate_limit_headers.items():
                response.headers[header] = value
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct IP
        return request.client.host
    
    async def _log_request(self, request: Request, response: Response, duration: float):
        """Log request for security monitoring"""
        if not self.redis_client:
            return
        
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": str(request.url.path),
            "query": str(request.url.query),
            "status_code": response.status_code,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("User-Agent", ""),
            "duration": round(duration * 1000, 2),  # ms
            "user_id": getattr(request.state, 'user_id', None)
        }
        
        # Store in Redis with TTL (7 days)
        log_key = f"request_log:{int(time.time())}:{id(request)}"
        await self.redis_client.setex(log_key, 7 * 24 * 3600, json.dumps(log_data))
        
        # Check for suspicious activity
        await self._detect_suspicious_activity(request, response, log_data)
    
    async def _detect_suspicious_activity(self, request: Request, response: Response, log_data: Dict):
        """Detect and respond to suspicious activity"""
        client_ip = log_data["client_ip"]
        
        # Count failed requests in last hour
        if response.status_code in [401, 403, 429]:
            failed_key = f"failed_requests:{client_ip}"
            failed_count = await self.redis_client.incr(failed_key)
            await self.redis_client.expire(failed_key, 3600)  # 1 hour
            
            # Block IP if too many failed requests
            if failed_count > 50:  # Threshold
                await self.redis_client.setex(f"blocked_ip:{client_ip}", 3600, "1")  # Block for 1 hour
                logger.warning(f"Blocked IP {client_ip} due to suspicious activity")
        
        # Detect potential attacks
        path = log_data["path"]
        query = log_data["query"]
        
        # SQL injection patterns
        sql_patterns = ["'", "union", "select", "drop", "insert", "update", "delete", "--", "/*"]
        if any(pattern in path.lower() or pattern in query.lower() for pattern in sql_patterns):
            logger.warning(f"Potential SQL injection from {client_ip}: {path}?{query}")
        
        # XSS patterns
        xss_patterns = ["<script", "javascript:", "onload=", "onerror="]
        if any(pattern in path.lower() or pattern in query.lower() for pattern in xss_patterns):
            logger.warning(f"Potential XSS attack from {client_ip}: {path}?{query}")

class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware"""
    
    def __init__(self, app, secret_key: str = "your-csrf-secret-key"):
        super().__init__(app)
        self.secret_key = secret_key.encode()
        self.safe_methods = {"GET", "HEAD", "OPTIONS", "TRACE"}
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """CSRF protection dispatcher"""
        
        # Skip CSRF for safe methods and API endpoints with proper auth
        if (request.method in self.safe_methods or 
            request.url.path.startswith("/api/") or
            request.url.path.startswith("/docs") or
            request.url.path.startswith("/openapi.json")):
            
            response = await call_next(request)
            
            # Add CSRF token to response for forms
            if request.method == "GET" and "text/html" in request.headers.get("accept", ""):
                csrf_token = self._generate_csrf_token()
                response.headers["X-CSRF-Token"] = csrf_token
            
            return response
        
        # Validate CSRF token for state-changing requests
        csrf_token = (request.headers.get("X-CSRF-Token") or 
                     request.headers.get("X-CSRFToken"))
        
        if not csrf_token or not self._validate_csrf_token(csrf_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing or invalid"
            )
        
        return await call_next(request)
    
    def _generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        timestamp = str(int(time.time()))
        message = f"csrf-{timestamp}"
        signature = hmac.new(
            self.secret_key,
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{timestamp}.{signature}"
    
    def _validate_csrf_token(self, token: str) -> bool:
        """Validate CSRF token"""
        try:
            timestamp_str, signature = token.split(".")
            timestamp = int(timestamp_str)
            
            # Check if token is not too old (1 hour)
            if time.time() - timestamp > 3600:
                return False
            
            # Verify signature
            message = f"csrf-{timestamp_str}"
            expected_signature = hmac.new(
                self.secret_key,
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except (ValueError, TypeError):
            return False

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Request validation and sanitization middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        
        # Blocked user agents (bots, scanners)
        self.blocked_user_agents = [
            "sqlmap", "nikto", "nmap", "masscan", "zap",
            "burp", "dirbuster", "gobuster", "ffuf"
        ]
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Request validation dispatcher"""
        
        # Check user agent
        user_agent = request.headers.get("User-Agent", "").lower()
        if any(blocked in user_agent for blocked in self.blocked_user_agents):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Blocked user agent"
            )
        
        # Validate content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("Content-Type", "")
            
            # Only allow specific content types
            allowed_types = [
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data",
                "text/plain"
            ]
            
            if not any(allowed_type in content_type for allowed_type in allowed_types):
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="Unsupported content type"
                )
        
        return await call_next(request)

def setup_security_middleware(app, redis_url: str = "redis://localhost:6379"):
    """Setup all security middleware"""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "https://yourdomain.com"],  # Configure for your frontend
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Request validation middleware
    app.add_middleware(RequestValidationMiddleware)
    
    # CSRF middleware
    app.add_middleware(CSRFMiddleware)
    
    # Main security middleware
    app.add_middleware(
        SecurityMiddleware,
        redis_url=redis_url,
        rate_limit_requests=1000,  # Adjust based on needs
        rate_limit_window=60,
        enable_csrf=True,
        max_request_size=10 * 1024 * 1024,  # 10MB
    )

# Additional security utilities
class SecurityUtils:
    """Security utility functions"""
    
    @staticmethod
    def sanitize_input(input_string: str) -> str:
        """Sanitize user input"""
        if not isinstance(input_string, str):
            return ""
        
        # Remove potentially dangerous characters
        dangerous_chars = ["<", ">", "'", "\"", "&", ";", "(", ")", "|", "`"]
        sanitized = input_string
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")
        
        return sanitized.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure token"""
        import secrets
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Hash sensitive data for logging"""
        return hashlib.sha256(data.encode()).hexdigest()[:8]  # First 8 chars for identification