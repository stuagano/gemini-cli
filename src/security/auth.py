"""
OAuth2 and RBAC Authentication System
Enterprise-grade security for Gemini Agent Server
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import secrets
import hashlib
import hmac
from urllib.parse import urlencode, parse_qs
import base64

import jwt
from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import httpx
import redis.asyncio as redis

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = "your-secret-key-change-in-production"  # Should be from environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)
security = HTTPBearer(auto_error=False)

class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"
    AGENT = "agent"
    SYSTEM = "system"

class Permission(str, Enum):
    """Permissions for granular access control"""
    # Agent permissions
    AGENT_READ = "agent:read"
    AGENT_WRITE = "agent:write"
    AGENT_EXECUTE = "agent:execute"
    AGENT_ADMIN = "agent:admin"
    
    # Data permissions
    DATA_READ = "data:read"
    DATA_WRITE = "data:write"
    DATA_DELETE = "data:delete"
    
    # System permissions
    SYSTEM_READ = "system:read"
    SYSTEM_WRITE = "system:write"
    SYSTEM_ADMIN = "system:admin"
    
    # Monitoring permissions
    METRICS_READ = "metrics:read"
    METRICS_WRITE = "metrics:write"
    
    # DORA permissions
    DORA_READ = "dora:read"
    DORA_WRITE = "dora:write"

# Role-permission mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.AGENT_READ, Permission.AGENT_WRITE, Permission.AGENT_EXECUTE, Permission.AGENT_ADMIN,
        Permission.DATA_READ, Permission.DATA_WRITE, Permission.DATA_DELETE,
        Permission.SYSTEM_READ, Permission.SYSTEM_WRITE, Permission.SYSTEM_ADMIN,
        Permission.METRICS_READ, Permission.METRICS_WRITE,
        Permission.DORA_READ, Permission.DORA_WRITE
    ],
    UserRole.DEVELOPER: [
        Permission.AGENT_READ, Permission.AGENT_WRITE, Permission.AGENT_EXECUTE,
        Permission.DATA_READ, Permission.DATA_WRITE,
        Permission.SYSTEM_READ,
        Permission.METRICS_READ,
        Permission.DORA_READ, Permission.DORA_WRITE
    ],
    UserRole.VIEWER: [
        Permission.AGENT_READ,
        Permission.DATA_READ,
        Permission.SYSTEM_READ,
        Permission.METRICS_READ,
        Permission.DORA_READ
    ],
    UserRole.AGENT: [
        Permission.AGENT_READ, Permission.AGENT_EXECUTE,
        Permission.DATA_READ, Permission.DATA_WRITE,
        Permission.METRICS_WRITE,
        Permission.DORA_WRITE
    ],
    UserRole.SYSTEM: [
        Permission.SYSTEM_READ, Permission.SYSTEM_WRITE,
        Permission.METRICS_READ, Permission.METRICS_WRITE,
        Permission.DORA_READ, Permission.DORA_WRITE
    ]
}

class User(BaseModel):
    """User model"""
    id: str
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None
    permissions: List[Permission] = []

class UserCreate(BaseModel):
    """User creation model"""
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.VIEWER

class UserUpdate(BaseModel):
    """User update model"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class Token(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    """Token data model"""
    user_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[UserRole] = None
    permissions: List[Permission] = []

class OAuth2Provider(BaseModel):
    """OAuth2 provider configuration"""
    name: str
    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    user_info_url: str
    scopes: List[str]

class AuthManager:
    """Authentication and authorization manager"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.oauth2_providers = {}
        
        # Initialize OAuth2 providers
        self._init_oauth2_providers()
    
    async def initialize(self):
        """Initialize the auth manager"""
        self.redis_client = redis.from_url(self.redis_url)
        await self._create_default_users()
    
    def _init_oauth2_providers(self):
        """Initialize OAuth2 providers"""
        # Google OAuth2
        self.oauth2_providers['google'] = OAuth2Provider(
            name="Google",
            client_id="your-google-client-id",
            client_secret="your-google-client-secret",
            authorize_url="https://accounts.google.com/o/oauth2/auth",
            token_url="https://oauth2.googleapis.com/token",
            user_info_url="https://www.googleapis.com/oauth2/v2/userinfo",
            scopes=["openid", "email", "profile"]
        )
        
        # GitHub OAuth2
        self.oauth2_providers['github'] = OAuth2Provider(
            name="GitHub",
            client_id="your-github-client-id",
            client_secret="your-github-client-secret",
            authorize_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            user_info_url="https://api.github.com/user",
            scopes=["user:email"]
        )
    
    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create an access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create a refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    async def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode a token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            username: str = payload.get("username")
            role: str = payload.get("role")
            
            if user_id is None or username is None:
                return None
            
            # Check if token is blacklisted
            if await self._is_token_blacklisted(token):
                return None
            
            # Get user permissions
            permissions = ROLE_PERMISSIONS.get(UserRole(role), [])
            
            return TokenData(
                user_id=user_id,
                username=username,
                role=UserRole(role),
                permissions=permissions
            )
        except jwt.PyJWTError:
            return None
    
    async def _is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        if not self.redis_client:
            return False
        
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return await self.redis_client.exists(f"blacklist:{token_hash}")
    
    async def blacklist_token(self, token: str, ttl_seconds: int = None):
        """Blacklist a token"""
        if not self.redis_client:
            return
        
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        if ttl_seconds:
            await self.redis_client.setex(f"blacklist:{token_hash}", ttl_seconds, "1")
        else:
            await self.redis_client.set(f"blacklist:{token_hash}", "1")
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        user_id = secrets.token_urlsafe(16)
        hashed_password = self.hash_password(user_data.password)
        
        user = User(
            id=user_id,
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            role=user_data.role,
            created_at=datetime.utcnow(),
            permissions=ROLE_PERMISSIONS.get(user_data.role, [])
        )
        
        # Store user in Redis (in production, use a proper database)
        user_data = user.dict()
        user_data['password_hash'] = hashed_password
        user_data['created_at'] = user_data['created_at'].isoformat()
        if user_data['last_login']:
            user_data['last_login'] = user_data['last_login'].isoformat()
        
        await self.redis_client.hset(f"user:{user_id}", mapping=user_data)
        await self.redis_client.hset(f"user:email:{user.email}", "user_id", user_id)
        await self.redis_client.hset(f"user:username:{user.username}", "user_id", user_id)
        
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        if not self.redis_client:
            return None
        
        user_data = await self.redis_client.hgetall(f"user:{user_id}")
        if not user_data:
            return None
        
        # Convert bytes to strings and parse dates
        user_dict = {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v 
                    for k, v in user_data.items()}
        
        if 'created_at' in user_dict:
            user_dict['created_at'] = datetime.fromisoformat(user_dict['created_at'])
        if 'last_login' in user_dict and user_dict['last_login']:
            user_dict['last_login'] = datetime.fromisoformat(user_dict['last_login'])
        
        # Remove password hash
        user_dict.pop('password_hash', None)
        
        return User(**user_dict)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        if not self.redis_client:
            return None
        
        user_id = await self.redis_client.hget(f"user:email:{email}", "user_id")
        if not user_id:
            return None
        
        return await self.get_user_by_id(user_id.decode() if isinstance(user_id, bytes) else user_id)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user"""
        user = await self.get_user_by_email(username)
        if not user:
            return None
        
        # Get password hash
        user_data = await self.redis_client.hgetall(f"user:{user.id}")
        password_hash = user_data.get(b'password_hash') or user_data.get('password_hash')
        
        if isinstance(password_hash, bytes):
            password_hash = password_hash.decode()
        
        if not self.verify_password(password, password_hash):
            return None
        
        # Update last login
        await self.redis_client.hset(f"user:{user.id}", "last_login", datetime.utcnow().isoformat())
        
        return user
    
    async def login(self, username: str, password: str) -> Optional[Token]:
        """Login user and return tokens"""
        user = await self.authenticate_user(username, password)
        if not user:
            return None
        
        # Create tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": user.id, "username": user.username, "role": user.role.value},
            expires_delta=access_token_expires
        )
        refresh_token = self.create_refresh_token(
            data={"sub": user.id, "username": user.username, "role": user.role.value}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    def generate_oauth2_url(self, provider: str, redirect_uri: str, state: str = None) -> str:
        """Generate OAuth2 authorization URL"""
        if provider not in self.oauth2_providers:
            raise ValueError(f"Unknown OAuth2 provider: {provider}")
        
        oauth_provider = self.oauth2_providers[provider]
        
        params = {
            "client_id": oauth_provider.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(oauth_provider.scopes),
            "response_type": "code"
        }
        
        if state:
            params["state"] = state
        
        return f"{oauth_provider.authorize_url}?{urlencode(params)}"
    
    async def handle_oauth2_callback(self, provider: str, code: str, redirect_uri: str) -> Optional[Token]:
        """Handle OAuth2 callback and create user session"""
        if provider not in self.oauth2_providers:
            raise ValueError(f"Unknown OAuth2 provider: {provider}")
        
        oauth_provider = self.oauth2_providers[provider]
        
        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                oauth_provider.token_url,
                data={
                    "client_id": oauth_provider.client_id,
                    "client_secret": oauth_provider.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                },
                headers={"Accept": "application/json"}
            )
            
            if token_response.status_code != 200:
                logger.error(f"OAuth2 token exchange failed: {token_response.text}")
                return None
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                logger.error("No access token in OAuth2 response")
                return None
            
            # Get user info
            user_response = await client.get(
                oauth_provider.user_info_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if user_response.status_code != 200:
                logger.error(f"OAuth2 user info request failed: {user_response.text}")
                return None
            
            user_info = user_response.json()
        
        # Extract user data based on provider
        if provider == "google":
            email = user_info.get("email")
            username = user_info.get("email")
            full_name = user_info.get("name")
        elif provider == "github":
            email = user_info.get("email")
            username = user_info.get("login")
            full_name = user_info.get("name")
        else:
            return None
        
        if not email:
            logger.error("No email in OAuth2 user info")
            return None
        
        # Check if user exists
        user = await self.get_user_by_email(email)
        if not user:
            # Create new user
            user_create = UserCreate(
                email=email,
                username=username,
                password=secrets.token_urlsafe(32),  # Random password for OAuth users
                full_name=full_name,
                role=UserRole.DEVELOPER  # Default role for OAuth users
            )
            user = await self.create_user(user_create)
        
        # Create tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": user.id, "username": user.username, "role": user.role.value},
            expires_delta=access_token_expires
        )
        refresh_token = self.create_refresh_token(
            data={"sub": user.id, "username": user.username, "role": user.role.value}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def _create_default_users(self):
        """Create default users if they don't exist"""
        # Admin user
        admin_user = await self.get_user_by_email("admin@gemini.local")
        if not admin_user:
            admin_create = UserCreate(
                email="admin@gemini.local",
                username="admin",
                password="admin123",  # Change in production
                full_name="System Administrator",
                role=UserRole.ADMIN
            )
            await self.create_user(admin_create)
            logger.info("Created default admin user")
        
        # System user for agents
        system_user = await self.get_user_by_email("system@gemini.local")
        if not system_user:
            system_create = UserCreate(
                email="system@gemini.local",
                username="system",
                password=secrets.token_urlsafe(32),
                full_name="System Agent",
                role=UserRole.SYSTEM
            )
            await self.create_user(system_create)
            logger.info("Created default system user")

# Global auth manager instance
auth_manager = AuthManager()

# Permission checking functions
def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get current user from dependency injection
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if permission not in current_user.permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission.value}' required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(role: UserRole):
    """Decorator to require specific role"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if current_user.role != role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{role.value}' required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# FastAPI dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[User]:
    """Get current user from JWT token"""
    if not credentials:
        return None
    
    token_data = await auth_manager.verify_token(credentials.credentials)
    if not token_data:
        return None
    
    user = await auth_manager.get_user_by_id(token_data.user_id)
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current admin user"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# API key authentication for agents
class APIKeyAuth:
    """API Key authentication for agent-to-agent communication"""
    
    def __init__(self):
        self.api_keys = {}
    
    async def create_api_key(self, user_id: str, name: str, permissions: List[Permission]) -> str:
        """Create an API key"""
        api_key = f"gea_{secrets.token_urlsafe(32)}"
        
        key_data = {
            "user_id": user_id,
            "name": name,
            "permissions": [p.value for p in permissions],
            "created_at": datetime.utcnow().isoformat(),
            "last_used": None
        }
        
        # Store in Redis
        await auth_manager.redis_client.hset(f"api_key:{api_key}", mapping=key_data)
        
        return api_key
    
    async def verify_api_key(self, api_key: str) -> Optional[Dict]:
        """Verify an API key"""
        if not api_key.startswith("gea_"):
            return None
        
        key_data = await auth_manager.redis_client.hgetall(f"api_key:{api_key}")
        if not key_data:
            return None
        
        # Update last used
        await auth_manager.redis_client.hset(f"api_key:{api_key}", "last_used", datetime.utcnow().isoformat())
        
        return {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v 
                for k, v in key_data.items()}

# Global API key auth instance
api_key_auth = APIKeyAuth()