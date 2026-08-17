"""Authentication, Registration, and Token Lifecycle API endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from openquant.domain.models.auth import User, UserRole
from openquant.domain.exceptions import AuthenticationError, UserAlreadyExistsError
from openquant.application.services.auth_service import auth_service
from openquant.interfaces.api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    role: UserRole = UserRole.TRADER


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: str
    permissions: list[str]


@router.post("/register", status_code=status.HTTP_201_CREATED, summary="Register User")
async def register(req: RegisterRequest) -> dict:
    """Register a new user account."""
    try:
        user = await auth_service.register_user(
            email=req.email,
            password=req.password,
            full_name=req.full_name,
            role=req.role,
        )
        return {
            "message": "User registered successfully",
            "user": {
                "user_id": user.user_id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
            },
        }
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", summary="User Login")
async def login(req: LoginRequest) -> dict:
    """Authenticate with email/password and obtain JWT access + refresh tokens."""
    try:
        return await auth_service.authenticate_user(req.email, req.password)
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", summary="Refresh Access Token")
async def refresh_token(req: RefreshRequest) -> dict:
    """Exchange a valid refresh token for a newly issued access token."""
    try:
        return await auth_service.refresh_access_token(req.refresh_token)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me", response_model=UserResponse, summary="Get Current User Profile")
async def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    """Fetch profile, role, and granular permissions of the authenticated user."""
    return UserResponse(
        user_id=current_user.user_id,
        email=str(current_user.email),
        full_name=current_user.full_name,
        role=current_user.role.value,
        permissions=[p.value for p in current_user.permissions],
    )
