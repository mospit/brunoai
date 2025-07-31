"""
Authentication API routes.
"""

import random
import string
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_active_user,
    get_password_hash,
    get_user_by_email,
    get_user_from_refresh_token,
)
from ..services.firebase_service import firebase_service
from ..database import get_async_session
from ..models.user import Household, HouseholdMember, User
from ..schemas import (
    HouseholdCreate,
    HouseholdResponse,
    RefreshTokenRequest,
    RegistrationToken,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)

router = APIRouter(prefix="/users", tags=["authentication"])


def generate_invite_code() -> str:
    """Generate an 8-digit invite code for households."""
    return ''.join(random.choices(string.digits, k=8))


@router.post("/register", response_model=RegistrationToken, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_session),
):
    """Register a new user with Firebase Authentication integration."""
    # Check if user already exists in PostgreSQL
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user in Firebase Authentication first
    firebase_uid = None
    if firebase_service.is_initialized():
        firebase_uid = await firebase_service.create_user(
            email=user_data.email,
            password=user_data.password,
            name=user_data.name
        )
        
        if not firebase_uid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user in Firebase Authentication"
            )
    else:
        # Log warning if Firebase is not available
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Firebase not initialized - creating user without Firebase integration")

    # Create new user in PostgreSQL with Firebase UID
    db_user = User(
        email=user_data.email,
        name=user_data.name,
        firebase_uid=firebase_uid,
        is_active=True,
        is_verified=False,  # Firebase handles email verification
    )

    try:
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
    except Exception as e:
        # If PostgreSQL user creation fails, clean up Firebase user
        if firebase_uid and firebase_service.is_initialized():
            await firebase_service.delete_user(firebase_uid)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

    # Create default household for the user
    invite_code = generate_invite_code()

    # Ensure invite code is unique
    while True:
        result = await db.execute(
            select(Household).where(Household.invite_code == invite_code)
        )
        if not result.scalar_one_or_none():
            break
        invite_code = generate_invite_code()

    household = Household(
        name=f"{db_user.name}'s Household",
        invite_code=invite_code,
        admin_user_id=db_user.id,
    )

    db.add(household)
    await db.commit()
    await db.refresh(household)

    # Add user as admin member of their household
    member = HouseholdMember(
        user_id=db_user.id,
        household_id=household.id,
        role="admin",
    )

    db.add(member)
    await db.commit()
    
    # Create tokens for the new user
    access_token_expires = timedelta(minutes=15)
    access_token = create_access_token(
        data={"sub": str(db_user.id)}, expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(days=7)
    refresh_token = create_refresh_token(
        data={"sub": str(db_user.id)}, expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": db_user
    }


@router.post("/login", response_model=Token)
async def login_user(
    user_data: UserLogin,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_session),
):
    """Login user and return JWT tokens using Firebase Authentication."""
    from ..services.security_service import security_service
    from ..services.cookie_service import cookie_service
    
    # Get client IP for rate limiting
    client_ip = security_service.get_client_ip(request)
    
    # Sanitize input data
    sanitized_data = security_service.sanitize_request_data({
        "email": user_data.email,
        "password": user_data.password
    })
    
    # Authenticate user using Firebase if available
    firebase_auth_result = None
    if firebase_service.is_initialized():
        firebase_auth_result = await firebase_service.authenticate_user_with_password(
            sanitized_data["email"], sanitized_data["password"]
        )

        if not firebase_auth_result:
            # Record failed authentication attempt for rate limiting
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not firebase_auth_result.get('verified', True):  # Default to True if key doesn't exist
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not verified"
            )
    else:
        # Log warning if Firebase is not available
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Firebase not initialized - skipping Firebase authentication")

    # Retrieve the user from the database
    user = await get_user_by_email(db, sanitized_data["email"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # Create 15-minute access token
    access_token_expires = timedelta(minutes=15)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    # Create 7-day refresh token
    refresh_token_expires = timedelta(days=7)
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}, expires_delta=refresh_token_expires
    )
    
    # Set secure cookies if using cookie-based auth
    cookie_service.set_auth_cookies(
        response, request, access_token, refresh_token
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """Refresh access token using refresh token."""
    # Verify refresh token and get user
    user = await get_user_from_refresh_token(token_data.refresh_token, db)

    # Create new 15-minute access token
    access_token_expires = timedelta(minutes=15)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/csrf-token")
async def get_csrf_token(request: Request):
    """Get CSRF token for the session."""
    from ..services.security_service import security_service
    from ..services.cookie_service import cookie_service
    
    session_id = cookie_service.get_session_id_from_cookie(request)
    csrf_token = security_service.generate_csrf_token(session_id)
    
    return {
        "csrf_token": csrf_token
    }


@router.post("/logout")
async def logout_user(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Logout user and clear cookies."""
    from ..services.cookie_service import cookie_service
    from ..services.security_service import security_service
    from ..services.auth_service import auth_service
    
    # Revoke all refresh tokens for the user
    await auth_service.revoke_all_user_tokens(db, current_user.id)
    
    # Clear authentication cookies
    cookie_service.clear_auth_cookies(response, request)
    
    # Log the logout event
    security_service.logger.log_auth_attempt(
        request, current_user.email, True, "logout", str(current_user.id)
    )
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    """Get current user information."""
    return current_user


@router.get("/households", response_model=list[HouseholdResponse])
async def get_user_households(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get households the current user is a member of."""
    result = await db.execute(
        select(Household)
        .join(HouseholdMember)
        .where(HouseholdMember.user_id == current_user.id)
    )
    households = result.scalars().all()
    return households


@router.post("/households", response_model=HouseholdResponse)
async def create_household(
    household_data: HouseholdCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Create a new household."""
    # Generate unique invite code
    invite_code = generate_invite_code()

    while True:
        result = await db.execute(
            select(Household).where(Household.invite_code == invite_code)
        )
        if not result.scalar_one_or_none():
            break
        invite_code = generate_invite_code()

    # Create household
    household = Household(
        name=household_data.name,
        invite_code=invite_code,
        admin_user_id=current_user.id,
    )

    db.add(household)
    await db.commit()
    await db.refresh(household)

    # Add user as admin member
    member = HouseholdMember(
        user_id=current_user.id,
        household_id=household.id,
        role="admin",
    )

    db.add(member)
    await db.commit()

    return household


@router.post("/households/{invite_code}/join", response_model=HouseholdResponse)
async def join_household(
    invite_code: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Join a household using invite code."""
    # Find household by invite code
    result = await db.execute(
        select(Household).where(Household.invite_code == invite_code)
    )
    household = result.scalar_one_or_none()

    if not household:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invite code"
        )

    # Check if user is already a member
    result = await db.execute(
        select(HouseholdMember).where(
            HouseholdMember.user_id == current_user.id,
            HouseholdMember.household_id == household.id,
        )
    )
    existing_member = result.scalar_one_or_none()

    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a member of this household"
        )

    # Add user as member
    member = HouseholdMember(
        user_id=current_user.id,
        household_id=household.id,
        role="member",
    )

    db.add(member)
    await db.commit()

    return household


# Backwards compatibility router for old /auth endpoints
compat_router = APIRouter(prefix="/auth", tags=["authentication-legacy"], include_in_schema=False)


@compat_router.post("/register")
async def register_user_legacy(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_session),
):
    """Legacy endpoint - redirects to /api/users/register."""
    return await register_user(user_data, db)


@compat_router.post("/login")
async def login_user_legacy(
    user_data: UserLogin,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_session),
):
    """Legacy endpoint - redirects to /api/users/login."""
    return await login_user(user_data, request, response, db)


@compat_router.post("/refresh")
async def refresh_access_token_legacy(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """Legacy endpoint - redirects to /api/users/refresh."""
    return await refresh_access_token(token_data, db)


@compat_router.get("/csrf-token")
async def get_csrf_token_legacy(request: Request):
    """Legacy endpoint - redirects to /api/users/csrf-token."""
    return await get_csrf_token(request)


@compat_router.post("/logout")
async def logout_user_legacy(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Legacy endpoint - redirects to /api/users/logout."""
    return await logout_user(request, response, current_user, db)
