"""
Authentication middleware for Global ID Management System
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from typing import Optional
import logging

from .models import get_session, SessionData, UserRole, get_user_permissions

logger = logging.getLogger(__name__)

class AuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Skip auth for static files, API docs, and login page
            if self.should_skip_auth(request.url.path):
                await self.app(scope, receive, send)
                return
            
            # Check authentication
            session_data = self.get_current_user(request)
            
            # If no session and accessing protected route, redirect to login
            if not session_data and self.requires_auth(request.url.path):
                response = RedirectResponse(
                    url=self.get_login_url(request),
                    status_code=status.HTTP_302_FOUND
                )
                await response(scope, receive, send)
                return
            
            # Check permissions for authenticated users
            if session_data and not self.has_permission(session_data, request.url.path):
                response = RedirectResponse(
                    url=self.get_unauthorized_url(request),
                    status_code=status.HTTP_302_FOUND
                )
                await response(scope, receive, send)
                return
            
            # Add user data to request state
            if session_data:
                scope["state"] = {"user": session_data}
        
        await self.app(scope, receive, send)

    def should_skip_auth(self, path: str) -> bool:
        """Check if path should skip authentication"""
        skip_paths = [
            "/static/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/login",
            "/api/v1/auth/login",
            "/gid/static/",
            "/gid/docs",
            "/gid/redoc",
            "/gid/login",
            "/gid/api/v1/auth/login"
        ]
        
        return any(path.startswith(skip_path) for skip_path in skip_paths)

    def requires_auth(self, path: str) -> bool:
        """Check if path requires authentication"""
        # All paths require auth except those in should_skip_auth
        return not self.should_skip_auth(path)

    def get_current_user(self, request: Request) -> Optional[SessionData]:
        """Get current user from session"""
        # Try to get session token from cookie
        session_token = request.cookies.get("session_token")
        if session_token:
            return get_session(session_token)
        return None

    def has_permission(self, session_data: SessionData, path: str) -> bool:
        """Check if user has permission to access path"""
        permissions = get_user_permissions(session_data.role)
        
        # Extract page name from path
        page = self.extract_page_from_path(path)
        
        # Check if user can access this page
        return page in permissions["pages"]

    def extract_page_from_path(self, path: str) -> str:
        """Extract page name from URL path"""
        # Remove /gid/ prefix if present
        if path.startswith("/gid/"):
            path = path[5:]
        
        # Remove leading slash
        if path.startswith("/"):
            path = path[1:]
        
        # Map paths to page names
        if path == "" or path == "dashboard":
            return "dashboard"
        elif path.startswith("database-explorer"):
            return "database-explorer"
        elif path.startswith("upload"):
            return "upload"
        elif path.startswith("sync"):
            return "sync"
        elif path.startswith("monitoring"):
            return "monitoring"
        else:
            return "unknown"

    def get_login_url(self, request: Request) -> str:
        """Get login URL based on current path"""
        if "/gid/" in str(request.url):
            return "/gid/login"
        else:
            return "/login"

    def get_unauthorized_url(self, request: Request) -> str:
        """Get unauthorized URL based on current path"""
        if "/gid/" in str(request.url):
            return "/gid/unauthorized"
        else:
            return "/unauthorized"