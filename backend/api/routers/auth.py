# Phase 5: Authentication Router
# User registration, login, and authentication endpoints

from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from typing import Optional
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.schemas import UserCreate, UserLogin, UserResponse, Token, ErrorResponse
from models.database import User, get_engine
from services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

security = HTTPBearer()

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://brandpulse:brandpulse_dev_password@localhost:5433/brandpulse"
)


def get_db_session():
    """Dependency to get database session"""
    engine = get_engine(DATABASE_URL)
    with Session(engine) as session:
        yield session


# ============================================================================
# POST /auth/register - User Registration
# ============================================================================

@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="""
    Register a new user account.

    Requirements:
    - Email must be unique
    - Username must be unique
    - Password must be at least 8 characters

    Returns a JWT access token upon successful registration.
    """,
    responses={
        201: {"description": "User created successfully"},
        400: {"model": ErrorResponse, "description": "Email or username already exists"}
    }
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db_session)
) -> Token:
    """
    Register a new user.

    Args:
        user_data: User registration data (email, username, password)
        db: Database session

    Returns:
        JWT token and user information

    Raises:
        HTTPException: If email or username already exists
    """
    # Check if email already exists
    existing_user = db.exec(
        select(User).where(User.email == user_data.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if username already exists
    existing_username = db.exec(
        select(User).where(User.username == user_data.username)
    ).first()

    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # Hash the password
    hashed_password = AuthService.get_password_hash(user_data.password)

    # Create new user
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        is_active=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create access token
    access_token = AuthService.create_access_token(
        data={"sub": new_user.email}
    )

    # Return token and user info
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user)
    )


# ============================================================================
# POST /auth/login - User Login
# ============================================================================

@router.post(
    "/login",
    response_model=Token,
    summary="Login user",
    description="""
    Authenticate user and return JWT access token.

    The token should be included in subsequent requests as:
    `Authorization: Bearer <token>`
    """,
    responses={
        200: {"description": "Login successful"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"}
    }
)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db_session)
) -> Token:
    """
    Authenticate user and return JWT token.

    Args:
        login_data: User login credentials (email, password)
        db: Database session

    Returns:
        JWT token and user information

    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    user = db.exec(
        select(User).where(User.email == login_data.email)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not AuthService.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Create access token
    access_token = AuthService.create_access_token(
        data={"sub": user.email}
    )

    # Return token and user info
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


# ============================================================================
# GET /auth/me - Get Current User
# ============================================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_session)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.

    Args:
        credentials: HTTP authorization header with Bearer token
        db: Database session

    Returns:
        Current user object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    # Verify token and extract email
    email = AuthService.get_token_subject(token)

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

    # Find user
    user = db.exec(
        select(User).where(User.email == email)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="""
    Get information about the currently authenticated user.

    Requires valid JWT token in Authorization header.
    """,
    responses={
        200: {"description": "User information returned successfully"},
        401: {"model": ErrorResponse, "description": "Invalid or missing token"}
    }
)
def get_me(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Get current authenticated user information.

    Args:
        current_user: Current user (from JWT token)

    Returns:
        User information
    """
    return UserResponse.model_validate(current_user)
