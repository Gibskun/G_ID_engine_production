"""
Authentication routes for Global ID Management System
"""

from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import logging

from .models import (
    authenticate_user, create_session, invalidate_session, 
    get_session, LoginRequest, LoginResponse, get_user_permissions
)

logger = logging.getLogger(__name__)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Create auth router
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

@auth_router.post("/login", response_model=LoginResponse)
async def login_api(login_data: LoginRequest):
    """API endpoint for user login"""
    try:
        user = authenticate_user(login_data.username, login_data.password)
        
        if not user:
            return LoginResponse(
                success=False,
                message="Invalid username or password"
            )
        
        if not user.is_active:
            return LoginResponse(
                success=False,
                message="Account is disabled"
            )
        
        # Create session
        session_token = create_session(user)
        
        # Get user permissions
        permissions = get_user_permissions(user.role)
        
        return LoginResponse(
            success=True,
            message="Login successful",
            user={
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role.value,
                "permissions": permissions
            },
            session_token=session_token
        )
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return LoginResponse(
            success=False,
            message="An error occurred during login"
        )

@auth_router.post("/logout")
async def logout_api(request: Request):
    """API endpoint for user logout"""
    try:
        session_token = request.cookies.get("session_token")
        if session_token:
            invalidate_session(session_token)
        
        return {"success": True, "message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return {"success": False, "message": "Error during logout"}

@auth_router.get("/session")
async def get_session_info(request: Request):
    """Get current session information"""
    try:
        session_token = request.cookies.get("session_token")
        if not session_token:
            return {"authenticated": False}
        
        session_data = get_session(session_token)
        if not session_data:
            return {"authenticated": False}
        
        permissions = get_user_permissions(session_data.role)
        
        return {
            "authenticated": True,
            "user": {
                "username": session_data.username,
                "full_name": session_data.full_name,
                "role": session_data.role.value,
                "permissions": permissions
            }
        }
        
    except Exception as e:
        logger.error(f"Session info error: {str(e)}")
        return {"authenticated": False, "error": str(e)}