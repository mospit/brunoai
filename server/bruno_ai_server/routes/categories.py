"""
Category router for handling pantry categories.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from ..auth import get_current_active_user
from ..database import get_async_session
from ..models.pantry import PantryCategory
from ..models.user import User
from ..schemas import PantryCategoryResponse

# Define the router
router = APIRouter(prefix="/pantry/categories", tags=["categories"])


@router.get("/", response_model=List[PantryCategoryResponse])
async def get_categories(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Retrieve all available pantry categories."""
    result = await db.execute(
        select(PantryCategory).order_by(PantryCategory.name)
    )
    categories = result.scalars().all()
    return categories


@router.get("/{category_id}", response_model=PantryCategoryResponse)
async def get_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get a specific category by ID."""
    result = await db.execute(
        select(PantryCategory).where(PantryCategory.id == category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category


@router.get("/search/{search_term}", response_model=List[PantryCategoryResponse])
async def search_categories(
    search_term: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Search categories by name or description."""
    result = await db.execute(
        select(PantryCategory).where(
            PantryCategory.name.ilike(f"%{search_term}%") |
            PantryCategory.description.ilike(f"%{search_term}%")
        ).order_by(PantryCategory.name)
    )
    categories = result.scalars().all()
    return categories
