"""
Authentication models and utilities for Global ID Management System
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta
import hashlib
import secrets
from dataclasses import dataclass

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"

@dataclass
class User:
    username: str
    password_hash: str
    role: UserRole
    full_name: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True

class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: Optional[bool] = False

class LoginResponse(BaseModel):
    success: bool
    message: str
    user: Optional[dict] = None
    session_token: Optional[str] = None

class SessionData(BaseModel):
    username: str
    role: UserRole
    full_name: str
    created_at: datetime
    expires_at: datetime

# Hardcoded users as requested
HARDCODED_USERS = [
    User(
        username="superadmin",
        password_hash=hashlib.sha256("SuperAdmin@2025".encode()).hexdigest(),
        role=UserRole.SUPER_ADMIN,
        full_name="Super Administrator",
        created_at=datetime.now()
    ),
    User(
        username="admin",
        password_hash=hashlib.sha256("Admin@2025".encode()).hexdigest(),
        role=UserRole.ADMIN,
        full_name="System Administrator",
        created_at=datetime.now()
    ),
    User(
        username="user",
        password_hash=hashlib.sha256("User@2025".encode()).hexdigest(),
        role=UserRole.USER,
        full_name="Regular User",
        created_at=datetime.now()
    )
]

# In-memory session storage (for production, use Redis or database)
active_sessions = {}

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == password_hash

def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password"""
    for user in HARDCODED_USERS:
        if user.username == username and verify_password(password, user.password_hash):
            user.last_login = datetime.now()
            return user
    return None

def create_session_token() -> str:
    """Create a secure session token"""
    return secrets.token_urlsafe(32)

def create_session(user: User, remember_me: bool = False) -> str:
    """Create a new session for user"""
    token = create_session_token()
    
    # Set session duration based on remember_me
    if remember_me:
        expires_at = datetime.now() + timedelta(days=30)  # 30 days for remember me
    else:
        expires_at = datetime.now() + timedelta(hours=24)  # 24 hours for regular session
    
    session_data = SessionData(
        username=user.username,
        role=user.role,
        full_name=user.full_name,
        created_at=datetime.now(),
        expires_at=expires_at
    )
    active_sessions[token] = session_data
    return token

def get_session(token: str) -> Optional[SessionData]:
    """Get session data from token"""
    session = active_sessions.get(token)
    if session and datetime.now() < session.expires_at:
        return session
    elif session:
        # Clean up expired session
        del active_sessions[token]
    return None

def invalidate_session(token: str):
    """Invalidate a session"""
    if token in active_sessions:
        del active_sessions[token]

def get_user_permissions(role: UserRole) -> dict:
    """Get permissions for user role"""
    permissions = {
        UserRole.SUPER_ADMIN: {
            "pages": ["dashboard", "database-explorer", "upload", "sync", "monitoring"],
            "can_add": True,
            "can_delete": True,
            "can_edit": True,
            "can_view": True
        },
        UserRole.ADMIN: {
            "pages": ["dashboard", "database-explorer", "upload"],
            "can_add": True,
            "can_delete": True,
            "can_edit": True,
            "can_view": True
        },
        UserRole.USER: {
            "pages": ["dashboard", "database-explorer"],
            "can_add": False,
            "can_delete": False,
            "can_edit": False,
            "can_view": True
        }
    }
    return permissions.get(role, permissions[UserRole.USER])