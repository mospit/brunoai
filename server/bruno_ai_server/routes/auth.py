"""
Authentication API routes.
"""

import random
import string
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_active_user,
    get_current_user,
    get_password_hash,
    get_user_by_email,
    get_user_from_refresh_token,
)
from ..database import get_async_session
from ..models.user import User, Household, HouseholdMember
from ..schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    RefreshTokenRequest,
    HouseholdCreate,
    HouseholdResponse,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


def generate_invite_code() -> str:
    """Generate a 6-digit invite code for households."""
    return ''.join(random.choices(string.digits, k=6))


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_session),
):
    """Register a new user."""
    # Check if user already exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_active=True,
        is_verified=False,
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
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
        name=f"{db_user.full_name}'s Household",
        invite_code=invite_code,
        owner_id=db_user.id,
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
    
    return db_user


@router.post("/login", response_model=Token)
async def login_user(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_async_session),
):
    """Login user and return JWT tokens."""
    user = await authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
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
        owner_id=current_user.id,
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
