"""
GitHub Authentication and Authorization Manager
Handles GitHub App authentication, token management, and permission validation
"""

import os
import jwt
import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from cryptography.hazmat.primitives import serialization

import httpx
from cachetools import TTLCache
import redis.asyncio as redis

logger = logging.getLogger(__name__)

@dataclass
class GitHubPermissions:
    """GitHub App permissions"""
    contents: str = "read"
    issues: str = "write"
    pull_requests: str = "write"
    checks: str = "write"
    statuses: str = "write"
    metadata: str = "read"
    security_events: str = "write"
    vulnerability_alerts: str = "read"
    administration: str = "read"

@dataclass
class InstallationTokenData:
    """Installation token with metadata"""
    token: str
    expires_at: datetime
    permissions: GitHubPermissions
    installation_id: str
    repository_selection: str
    repositories: List[str] = field(default_factory=list)

class GitHubTokenCache:
    """Manages caching of GitHub tokens"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client = None
        self.memory_cache = TTLCache(maxsize=100, ttl=3600)  # 1 hour TTL
        
        if redis_url:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
    
    async def get_token(self, installation_id: str) -> Optional[InstallationTokenData]:
        """Get cached token for installation"""
        cache_key = f"github_token:{installation_id}"
        
        # Try Redis first
        if self.redis_client:
            try:
                token_data = await self.redis_client.hgetall(cache_key)
                if token_data:
                    expires_at = datetime.fromisoformat(token_data["expires_at"])
                    
                    # Check if token is still valid (with 5-minute buffer)
                    if expires_at > datetime.utcnow() + timedelta(minutes=5):
                        return InstallationTokenData(
                            token=token_data["token"],
                            expires_at=expires_at,
                            permissions=GitHubPermissions(**{
                                k: v for k, v in token_data.items() 
                                if k.startswith("perm_")
                            }),
                            installation_id=installation_id,
                            repository_selection=token_data.get("repository_selection", "all"),
                            repositories=token_data.get("repositories", "").split(",") if token_data.get("repositories") else []
                        )
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")
        
        # Fallback to memory cache
        return self.memory_cache.get(cache_key)
    
    async def set_token(self, installation_id: str, token_data: InstallationTokenData):
        """Cache token for installation"""
        cache_key = f"github_token:{installation_id}"
        
        # Calculate TTL (time until expiration minus 5-minute buffer)
        ttl_seconds = int((token_data.expires_at - datetime.utcnow() - timedelta(minutes=5)).total_seconds())
        
        if ttl_seconds <= 0:
            return  # Token already expired
        
        # Store in Redis
        if self.redis_client:
            try:
                cache_data = {
                    "token": token_data.token,
                    "expires_at": token_data.expires_at.isoformat(),
                    "installation_id": installation_id,
                    "repository_selection": token_data.repository_selection,
                    "repositories": ",".join(token_data.repositories),
                    **{f"perm_{k}": v for k, v in token_data.permissions.__dict__.items()}
                }
                
                pipe = self.redis_client.pipeline()
                pipe.hset(cache_key, mapping=cache_data)
                pipe.expire(cache_key, ttl_seconds)
                await pipe.execute()
                
                logger.info(f"Cached token for installation {installation_id} (TTL: {ttl_seconds}s)")
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")
        
        # Store in memory cache
        self.memory_cache[cache_key] = token_data
    
    async def invalidate_token(self, installation_id: str):
        """Invalidate cached token"""
        cache_key = f"github_token:{installation_id}"
        
        # Remove from Redis
        if self.redis_client:
            try:
                await self.redis_client.delete(cache_key)
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")
        
        # Remove from memory cache
        self.memory_cache.pop(cache_key, None)
        
        logger.info(f"Invalidated token cache for installation {installation_id}")

class GitHubAppAuthenticator:
    """GitHub App authentication manager"""
    
    def __init__(self, app_id: str, private_key: str, redis_url: Optional[str] = None):
        self.app_id = app_id
        self.private_key = serialization.load_pem_private_key(
            private_key.encode(), password=None
        )
        self.token_cache = GitHubTokenCache(redis_url)
        self.app_jwt_cache = {}  # Cache for app-level JWTs
    
    def generate_app_jwt(self) -> str:
        """Generate JWT for GitHub App authentication"""
        # Check cache first (JWTs are valid for 10 minutes)
        now = datetime.utcnow()
        cache_key = "app_jwt"
        
        if cache_key in self.app_jwt_cache:
            cached_jwt, expires_at = self.app_jwt_cache[cache_key]
            if expires_at > now + timedelta(minutes=1):  # 1-minute buffer
                return cached_jwt
        
        # Generate new JWT
        payload = {
            'iat': int(now.timestamp()),
            'exp': int((now + timedelta(minutes=10)).timestamp()),
            'iss': self.app_id
        }
        
        jwt_token = jwt.encode(payload, self.private_key, algorithm='RS256')
        
        # Cache the JWT
        self.app_jwt_cache[cache_key] = (jwt_token, now + timedelta(minutes=10))
        
        logger.debug("Generated new GitHub App JWT")
        return jwt_token
    
    async def get_installation_token(self, installation_id: str, force_refresh: bool = False) -> InstallationTokenData:
        """Get installation access token with caching"""
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_token = await self.token_cache.get_token(installation_id)
            if cached_token:
                logger.debug(f"Using cached token for installation {installation_id}")
                return cached_token
        
        # Generate new installation token
        app_jwt = self.generate_app_jwt()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.github.com/app/installations/{installation_id}/access_tokens",
                headers={
                    "Authorization": f"Bearer {app_jwt}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "Gemini-Enterprise-Architect/1.0"
                },
                timeout=30
            )
            
            if response.status_code != 201:
                logger.error(f"Failed to get installation token: {response.status_code} - {response.text}")
                raise Exception(f"Failed to get installation token: {response.status_code}")
            
            token_response = response.json()
            
            # Parse token data
            token_data = InstallationTokenData(
                token=token_response["token"],
                expires_at=datetime.fromisoformat(token_response["expires_at"].replace("Z", "+00:00")).replace(tzinfo=None),
                permissions=GitHubPermissions(**{
                    k: v for k, v in token_response.get("permissions", {}).items()
                    if hasattr(GitHubPermissions, k)
                }),
                installation_id=installation_id,
                repository_selection=token_response.get("repository_selection", "all"),
                repositories=[repo["name"] for repo in token_response.get("repositories", [])]
            )
            
            # Cache the token
            await self.token_cache.set_token(installation_id, token_data)
            
            logger.info(f"Generated new installation token for {installation_id}")
            return token_data
    
    async def get_installation_repositories(self, installation_id: str) -> List[Dict[str, Any]]:
        """Get repositories accessible by installation"""
        token_data = await self.get_installation_token(installation_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/installation/repositories",
                headers={
                    "Authorization": f"token {token_data.token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "Gemini-Enterprise-Architect/1.0"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("repositories", [])
            else:
                logger.error(f"Failed to get installation repositories: {response.status_code}")
                return []
    
    async def validate_repository_access(self, installation_id: str, repo_full_name: str) -> bool:
        """Validate if installation has access to repository"""
        try:
            repositories = await self.get_installation_repositories(installation_id)
            accessible_repos = [repo["full_name"] for repo in repositories]
            
            has_access = repo_full_name in accessible_repos
            logger.debug(f"Repository access check for {repo_full_name}: {has_access}")
            
            return has_access
        except Exception as e:
            logger.error(f"Error validating repository access: {e}")
            return False
    
    async def refresh_installation_token(self, installation_id: str) -> InstallationTokenData:
        """Force refresh of installation token"""
        await self.token_cache.invalidate_token(installation_id)
        return await self.get_installation_token(installation_id, force_refresh=True)

class PermissionValidator:
    """Validates GitHub App permissions for operations"""
    
    def __init__(self, authenticator: GitHubAppAuthenticator):
        self.authenticator = authenticator
    
    async def can_create_check_runs(self, installation_id: str) -> bool:
        """Check if app can create check runs"""
        try:
            token_data = await self.authenticator.get_installation_token(installation_id)
            return token_data.permissions.checks in ["write"]
        except Exception:
            return False
    
    async def can_update_statuses(self, installation_id: str) -> bool:
        """Check if app can update commit statuses"""
        try:
            token_data = await self.authenticator.get_installation_token(installation_id)
            return token_data.permissions.statuses in ["write"]
        except Exception:
            return False
    
    async def can_comment_on_prs(self, installation_id: str) -> bool:
        """Check if app can comment on pull requests"""
        try:
            token_data = await self.authenticator.get_installation_token(installation_id)
            return token_data.permissions.pull_requests in ["write"]
        except Exception:
            return False
    
    async def can_read_repository_contents(self, installation_id: str) -> bool:
        """Check if app can read repository contents"""
        try:
            token_data = await self.authenticator.get_installation_token(installation_id)
            return token_data.permissions.contents in ["read", "write"]
        except Exception:
            return False
    
    async def validate_operation_permissions(self, installation_id: str, operation: str) -> bool:
        """Validate permissions for specific operations"""
        permission_map = {
            "scaling_analysis": [self.can_read_repository_contents],
            "duplicate_detection": [self.can_read_repository_contents],
            "code_review": [self.can_read_repository_contents, self.can_comment_on_prs],
            "status_checks": [self.can_create_check_runs, self.can_update_statuses],
            "pr_comments": [self.can_comment_on_prs],
            "comprehensive_analysis": [
                self.can_read_repository_contents,
                self.can_comment_on_prs,
                self.can_create_check_runs
            ]
        }
        
        if operation not in permission_map:
            logger.warning(f"Unknown operation: {operation}")
            return False
        
        # Check all required permissions
        permission_checks = permission_map[operation]
        results = await asyncio.gather(*[check(installation_id) for check in permission_checks])
        
        has_permissions = all(results)
        logger.debug(f"Permission check for {operation}: {has_permissions}")
        
        return has_permissions

class RateLimitManager:
    """Manages GitHub API rate limiting"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client = None
        self.memory_limits = {}
        
        if redis_url:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
    
    async def check_rate_limit(self, installation_id: str) -> Dict[str, Any]:
        """Check current rate limit status"""
        # This would implement actual rate limit checking
        # For now, return a mock response
        return {
            "limit": 5000,
            "remaining": 4500,
            "reset": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            "used": 500
        }
    
    async def is_rate_limited(self, installation_id: str) -> bool:
        """Check if installation is currently rate limited"""
        rate_limit = await self.check_rate_limit(installation_id)
        return rate_limit["remaining"] < 100  # Conservative threshold
    
    async def wait_for_rate_limit_reset(self, installation_id: str, max_wait: int = 300):
        """Wait for rate limit reset (with maximum wait time)"""
        rate_limit = await self.check_rate_limit(installation_id)
        reset_time = datetime.fromtimestamp(rate_limit["reset"])
        wait_time = min((reset_time - datetime.utcnow()).total_seconds(), max_wait)
        
        if wait_time > 0:
            logger.info(f"Rate limited for installation {installation_id}, waiting {wait_time:.0f}s")
            await asyncio.sleep(wait_time)

# Configuration and factory functions
def create_github_authenticator(
    app_id: Optional[str] = None,
    private_key: Optional[str] = None,
    redis_url: Optional[str] = None
) -> GitHubAppAuthenticator:
    """Create GitHub authenticator with environment variables fallback"""
    app_id = app_id or os.environ.get("GITHUB_APP_ID")
    private_key = private_key or os.environ.get("GITHUB_PRIVATE_KEY")
    redis_url = redis_url or os.environ.get("REDIS_URL")
    
    if not app_id or not private_key:
        raise ValueError("GitHub App ID and private key are required")
    
    return GitHubAppAuthenticator(app_id, private_key, redis_url)

def create_permission_validator(authenticator: GitHubAppAuthenticator) -> PermissionValidator:
    """Create permission validator"""
    return PermissionValidator(authenticator)

def create_rate_limit_manager(redis_url: Optional[str] = None) -> RateLimitManager:
    """Create rate limit manager"""
    redis_url = redis_url or os.environ.get("REDIS_URL")
    return RateLimitManager(redis_url)

# Example usage and testing
async def test_authentication():
    """Test authentication functionality"""
    try:
        # Create authenticator
        auth = create_github_authenticator()
        
        # Test app JWT generation
        app_jwt = auth.generate_app_jwt()
        print(f"Generated app JWT: {app_jwt[:50]}...")
        
        # Test installation token (would need actual installation ID)
        # installation_id = "12345678"
        # token_data = await auth.get_installation_token(installation_id)
        # print(f"Installation token: {token_data.token[:50]}...")
        
        print("Authentication test completed successfully")
        
    except Exception as e:
        print(f"Authentication test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_authentication())