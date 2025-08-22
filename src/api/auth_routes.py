"""
Authentication routes for FastAPI
OAuth2, JWT, and RBAC endpoints
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import secrets

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, EmailStr

from security.auth import (
    auth_manager, api_key_auth,
    User, UserCreate, UserUpdate, Token, TokenData,
    UserRole, Permission,
    get_current_user, get_current_active_user, get_current_admin_user,
    require_permission, require_role
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# Request/Response models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User

class RefreshRequest(BaseModel):
    refresh_token: str

class OAuth2StartResponse(BaseModel):
    authorization_url: str
    state: str

class APIKeyCreateRequest(BaseModel):
    name: str
    permissions: List[Permission]

class APIKeyResponse(BaseModel):
    api_key: str
    name: str
    permissions: List[Permission]
    created_at: datetime

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

# Authentication endpoints
@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Login with username/password"""
    token = await auth_manager.login(login_data.username, login_data.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await auth_manager.get_user_by_email(login_data.username)
    
    return LoginResponse(
        access_token=token.access_token,
        refresh_token=token.refresh_token,
        token_type=token.token_type,
        expires_in=token.expires_in,
        user=user
    )

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token endpoint"""
    token = await auth_manager.login(form_data.username, form_data.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_data: RefreshRequest):
    """Refresh access token using refresh token"""
    try:
        token_data = await auth_manager.verify_token(refresh_data.refresh_token)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new tokens
        access_token_expires = timedelta(minutes=30)
        access_token = auth_manager.create_access_token(
            data={"sub": token_data.user_id, "username": token_data.username, "role": token_data.role.value},
            expires_delta=access_token_expires
        )
        refresh_token = auth_manager.create_refresh_token(
            data={"sub": token_data.user_id, "username": token_data.username, "role": token_data.role.value}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30 * 60
        )
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """Logout user (blacklist token)"""
    # In a real implementation, you'd blacklist the current token
    return {"message": "Successfully logged out"}

# User management endpoints
@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user info"""
    return current_user

@router.put("/me", response_model=User)
async def update_users_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update current user info"""
    # Update user data
    update_data = user_update.dict(exclude_unset=True)
    
    # Don't allow role changes through this endpoint
    update_data.pop('role', None)
    
    # Update user in storage (simplified for demo)
    for key, value in update_data.items():
        setattr(current_user, key, value)
    
    return current_user

@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Change user password"""
    # Verify current password
    user = await auth_manager.authenticate_user(current_user.email, password_data.current_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current password"
        )
    
    # Hash new password and update
    new_password_hash = auth_manager.hash_password(password_data.new_password)
    await auth_manager.redis_client.hset(
        f"user:{current_user.id}", 
        "password_hash", 
        new_password_hash
    )
    
    return {"message": "Password changed successfully"}

# OAuth2 endpoints
@router.get("/oauth2/{provider}/start", response_model=OAuth2StartResponse)
async def start_oauth2_flow(provider: str, redirect_uri: str):
    """Start OAuth2 authentication flow"""
    try:
        state = secrets.token_urlsafe(32)
        auth_url = auth_manager.generate_oauth2_url(provider, redirect_uri, state)
        
        # Store state for verification
        await auth_manager.redis_client.setex(f"oauth2_state:{state}", 600, provider)
        
        return OAuth2StartResponse(
            authorization_url=auth_url,
            state=state
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/oauth2/{provider}/callback")
async def oauth2_callback(
    provider: str,
    code: str,
    state: str,
    redirect_uri: str
):
    """Handle OAuth2 callback"""
    # Verify state
    stored_provider = await auth_manager.redis_client.get(f"oauth2_state:{state}")
    if not stored_provider or stored_provider.decode() != provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
    
    # Clean up state
    await auth_manager.redis_client.delete(f"oauth2_state:{state}")
    
    # Handle callback
    token = await auth_manager.handle_oauth2_callback(provider, code, redirect_uri)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth2 authentication failed"
        )
    
    return token

# Admin endpoints
@router.post("/users", response_model=User)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new user (admin only)"""
    # Check if user already exists
    existing_user = await auth_manager.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    user = await auth_manager.create_user(user_data)
    return user

@router.get("/users", response_model=List[User])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user)
):
    """List all users (admin only)"""
    # In a real implementation, you'd paginate through users
    # For now, return empty list
    return []

@router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Get user by ID (admin only)"""
    user = await auth_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    """Update user (admin only)"""
    user = await auth_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update user data
    update_data = user_update.dict(exclude_unset=True)
    
    # Update user in storage (simplified for demo)
    for key, value in update_data.items():
        setattr(user, key, value)
    
    return user

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Delete user (admin only)"""
    user = await auth_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow deleting self
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Delete user from storage
    await auth_manager.redis_client.delete(f"user:{user_id}")
    await auth_manager.redis_client.delete(f"user:email:{user.email}")
    await auth_manager.redis_client.delete(f"user:username:{user.username}")
    
    return {"message": "User deleted successfully"}

# API Key management
@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    api_key_data: APIKeyCreateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Create an API key"""
    # Verify user has permissions to create API key with these permissions
    for permission in api_key_data.permissions:
        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You don't have permission: {permission.value}"
            )
    
    api_key = await api_key_auth.create_api_key(
        user_id=current_user.id,
        name=api_key_data.name,
        permissions=api_key_data.permissions
    )
    
    return APIKeyResponse(
        api_key=api_key,
        name=api_key_data.name,
        permissions=api_key_data.permissions,
        created_at=datetime.utcnow()
    )

@router.get("/api-keys")
async def list_api_keys(current_user: User = Depends(get_current_active_user)):
    """List user's API keys"""
    # In a real implementation, you'd list the user's API keys
    return []

@router.delete("/api-keys/{api_key_id}")
async def revoke_api_key(
    api_key_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Revoke an API key"""
    # Delete API key
    await auth_manager.redis_client.delete(f"api_key:{api_key_id}")
    return {"message": "API key revoked successfully"}

# Permission and role management
@router.get("/permissions")
async def list_permissions(current_user: User = Depends(get_current_active_user)):
    """List all available permissions"""
    return [{"name": p.value, "description": p.value} for p in Permission]

@router.get("/roles")
async def list_roles(current_user: User = Depends(get_current_active_user)):
    """List all available roles and their permissions"""
    from security.auth import ROLE_PERMISSIONS
    
    roles = []
    for role, permissions in ROLE_PERMISSIONS.items():
        roles.append({
            "name": role.value,
            "permissions": [p.value for p in permissions]
        })
    
    return roles

@router.get("/me/permissions")
async def get_my_permissions(current_user: User = Depends(get_current_active_user)):
    """Get current user's permissions"""
    return {
        "role": current_user.role.value,
        "permissions": [p.value for p in current_user.permissions]
    }

# Health check
@router.get("/health")
async def auth_health_check():
    """Authentication service health check"""
    try:
        # Test Redis connection
        await auth_manager.redis_client.ping()
        
        return {
            "status": "healthy",
            "redis": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Rate limiting and security headers middleware would be added here
# For production, add:
# - Rate limiting per user/IP
# - CSRF protection
# - Security headers
# - Request logging
# - Input validation
# - SQL injection protection (if using SQL database)