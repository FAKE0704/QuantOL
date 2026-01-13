"""Authentication router for FastAPI.

Provides RESTful API endpoints for user authentication:
- POST /api/auth/login - User login
- POST /api/auth/register - User registration
- POST /api/auth/logout - User logout
- POST /api/auth/refresh - Refresh JWT token
- GET /api/auth/me - Get current user info
- GET /api/auth/registration-status - Check if registration is open
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr

from src.core.auth import AuthService
from src.database import get_db_adapter

# Router
router = APIRouter()

# Security
security = HTTPBearer()

# Pydantic models for request/response


class LoginRequest(BaseModel):
    """Login request model."""

    username_or_email: str
    password: str


class RegisterRequest(BaseModel):
    """Registration request model."""

    username: str
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Token refresh request model."""

    token: str


class LoginResponse(BaseModel):
    """Login response model."""

    success: bool
    message: str
    data: Optional[dict] = None


class UserResponse(BaseModel):
    """User info response model."""

    user_id: int
    username: str
    email: str
    role: str


class RegistrationStatusResponse(BaseModel):
    """Registration status response model."""

    allow_registration: bool
    user_count: int


# Dependencies


async def get_auth_service() -> AuthService:
    """Get auth service instance."""
    db = get_db_adapter()
    await db.initialize()
    return AuthService(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token credentials
        auth_service: Authentication service

    Returns:
        User info from token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    payload = await auth_service.verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return payload


# Endpoints


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """User login endpoint.

    Args:
        request: Login request with username/email and password
        auth_service: Authentication service

    Returns:
        Login response with user info and JWT token

    Raises:
        HTTPException: If login fails
    """
    result, message = await auth_service.login(
        request.username_or_email, request.password
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
        )

    return LoginResponse(success=True, message=message, data=result)


@router.post(
    "/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """User registration endpoint.

    Args:
        request: Registration request with username, email, and password
        auth_service: Authentication service

    Returns:
        Registration response

    Raises:
        HTTPException: If registration fails
    """
    success, message = await auth_service.register(
        request.username, request.email, request.password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return LoginResponse(success=True, message=message)


@router.post("/logout", response_model=LoginResponse)
async def logout(
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """User logout endpoint.

    Args:
        current_user: Current authenticated user
        auth_service: Authentication service

    Returns:
        Logout response
    """
    # Note: In a JWT-based system, logout is typically handled client-side
    # by deleting the token. Server-side logout can be implemented with
    # a token blacklist if needed.
    return LoginResponse(success=True, message="Logged out successfully")


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    request: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh JWT token endpoint.

    Args:
        request: Refresh request with old token
        auth_service: Authentication service

    Returns:
        Response with new token

    Raises:
        HTTPException: If token refresh fails
    """
    new_token = await auth_service.refresh_token(request.token)

    if new_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return LoginResponse(
        success=True, message="Token refreshed", data={"token": new_token}
    )


@router.get("/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
):
    """Get current user info endpoint.

    Args:
        current_user: Current authenticated user

    Returns:
        User info response in consistent API format
    """
    return {
        "success": True,
        "message": "User retrieved successfully",
        "data": {
            "user_id": current_user["user_id"],
            "username": current_user["username"],
            "email": current_user.get("email", ""),
            "role": current_user.get("role", "user"),
        }
    }


@router.get("/registration-status", response_model=RegistrationStatusResponse)
async def get_registration_status(
    auth_service: AuthService = Depends(get_auth_service),
):
    """Get registration status endpoint.

    Args:
        auth_service: Authentication service

    Returns:
        Registration status response
    """
    status_data = await auth_service.get_registration_status()

    return RegistrationStatusResponse(
        allow_registration=status_data.get("allow_registration", True),
        user_count=status_data.get("user_count", 0),
    )
