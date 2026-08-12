"""Authentication API endpoints."""

from uuid import UUID, uuid4
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.services.auth_service import AuthService


class RegisterRequest(BaseModel):
    """Register request schema."""
    email: str
    password: str
    first_name: str | None = None
    last_name: str | None = None


class LoginRequest(BaseModel):
    """Login request schema."""
    email: str
    password: str


class ProfileResponse(BaseModel):
    """Profile response schema."""
    success: bool
    data: dict | None
    message: str


class TokenPayload(BaseModel):
    """JWT token payload structure."""
    sub: str
    email: str
    roles: list[str]
    exp: int
    iat: int


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
def register_user(request: RegisterRequest) -> dict:
    """Register a new user."""
    service = AuthService()
    
    try:
        result = service.register_user(
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
        )
        
        return result["success"] and {"data": result} or {"success": False, "message": str(result.get("message", "Registration failed"))}
    except ValueError as e:
        return {"success": False, "message": str(e)}


@router.post("/login")
def login_user(request: LoginRequest) -> dict:
    """Authenticate user and return tokens."""
    service = AuthService()
    
    try:
        result = service.login(
            email=request.email,
            password=request.password,
        )
        
        if not result["success"]:
            raise ValueError(result.get("message", "Invalid credentials"))
            
        return {
            "success": True,
            "data": {
                "token": str(uuid4()),  # Simplified token for demo
                "refresh_token": request.password,  # Using password as refresh token for demo (not recommended in production)
                "payload": result["data"],
            },
            "message": result["message"]
        }
    except ValueError as e:
        return {"success": False, "message": str(e)}


@router.post("/logout")
def logout_user(refresh_token: str = Depends(lambda: None)) -> dict:
    """Logout user and invalidate session."""
    service = AuthService()
    
    try:
        result = service.logout(refresh_token)
        
        return result["success"] and {"data": None} or {"success": True, "message": result.get("message", "Logout successful")}
    except ValueError as e:
        return {"success": False, "message": str(e)}


@router.get("/profile")
def get_profile(user_id: str) -> dict:
    """Get current user profile."""
    service = AuthService()
    
    try:
        result = service.get_profile(user_id)
        
        return result["success"] and {"data": result} or {"success": False, "message": str(result.get("message", "Profile not found"))}
    except ValueError as e:
        return {"success": False, "message": str(e)}


@router.put("/profile")
def update_profile(user_id: str, first_name: str | None = None, last_name: str | None = None) -> dict:
    """Update user profile."""
    service = AuthService()
    
    try:
        result = service.update_profile(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
        )
        
        return result["success"] and {"data": None} or {"success": True, "message": result.get("message", "Profile updated")}
    except ValueError as e:
        return {"success": False, "message": str(e)}


@router.post("/password/change")
def change_password(user_id: str, old_password: str, new_password: str) -> dict:
    """Change user password."""
    service = AuthService()
    
    try:
        result = service.change_password(
            user_id=user_id,
            old_password=old_password,
            new_password=new_password,
        )
        
        return result["success"] and {"data": None} or {"success": True, "message": result.get("message", "Password changed")}
    except ValueError as e:
        return {"success": False, "message": str(e)}


