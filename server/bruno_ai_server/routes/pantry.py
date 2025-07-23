"""
Pantry router for handling pantry items.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Optional

from ..auth import get_current_active_user
from ..database import get_async_session
from ..models.pantry import PantryItem, PantryCategory
from ..models.user import User, HouseholdMember
from ..schemas import PantryItemCreate, PantryItemUpdate, PantryItemResponse

# Define the router
router = APIRouter(prefix="/pantry/items", tags=["pantry"])


async def get_user_household_id(user: User, db: AsyncSession) -> Optional[int]:
    """Get the user's primary household ID."""
    # First try to get household where user is an admin (most likely primary)
    result = await db.execute(
        select(HouseholdMember.household_id)
        .where(
            HouseholdMember.user_id == user.id,
            HouseholdMember.role == "admin"
        )
        .limit(1)
    )
    household_id = result.scalar_one_or_none()
    
    if household_id:
        return household_id
    
    # If no admin household, get any household the user is a member of
    result = await db.execute(
        select(HouseholdMember.household_id)
        .where(HouseholdMember.user_id == user.id)
        .limit(1)
    )
    return result.scalar_one_or_none()


@router.get("/", response_model=list[PantryItemResponse])
async def get_pantry_items(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
    category: str = Query(None, description="Filter by category"),
    search: str = Query(None, description="Search by keyword")
):
    """Retrieve all pantry items for the current user's household."""
    household_id = await get_user_household_id(current_user, db)
    if not household_id:
        raise HTTPException(status_code=400, detail="User is not a member of any household")
    
    query = select(PantryItem).where(PantryItem.household_id == household_id)
    
    if category:
        query = query.join(PantryCategory).where(PantryCategory.name == category)
    if search:
        query = query.where(PantryItem.name.ilike(f"%{search}%"))

    result = await db.execute(query.options(selectinload(PantryItem.category), selectinload(PantryItem.added_by_user)))
    items = result.scalars().all()
    return items


@router.post("/", response_model=PantryItemResponse)
async def create_pantry_item(
    pantry_item_data: PantryItemCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Create a new pantry item for the current user's household."""
    household_id = await get_user_household_id(current_user, db)
    if not household_id:
        raise HTTPException(status_code=400, detail="User is not a member of any household")
    
    pantry_item = PantryItem(
        **pantry_item_data.dict(),
        household_id=household_id,
        added_by_user_id=current_user.id
    )
    db.add(pantry_item)
    await db.commit()
    await db.refresh(pantry_item)
    return pantry_item


@router.put("/{item_id}", response_model=PantryItemResponse)
async def update_pantry_item(
    item_id: int,
    item_update_data: PantryItemUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Update an existing pantry item."""
    household_id = await get_user_household_id(current_user, db)
    if not household_id:
        raise HTTPException(status_code=400, detail="User is not a member of any household")
    
    # Fetch the existing pantry item
    result = await db.execute(
        select(PantryItem).options(selectinload(PantryItem.category), selectinload(PantryItem.added_by_user)).where(
            PantryItem.id == item_id,
            PantryItem.household_id == household_id)
    )
    pantry_item = result.scalar_one_or_none()
    
    if pantry_item is None:
        raise HTTPException(status_code=404, detail="Pantry item not found.")

    for key, value in item_update_data.dict(exclude_unset=True).items():
        setattr(pantry_item, key, value)

    await db.commit()
    await db.refresh(pantry_item)
    return pantry_item


@router.delete("/{item_id}", response_model=dict)
async def delete_pantry_item(
    item_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Delete a pantry item."""
    household_id = await get_user_household_id(current_user, db)
    if not household_id:
        raise HTTPException(status_code=400, detail="User is not a member of any household")
    
    # Fetch the existing pantry item
    result = await db.execute(
        select(PantryItem).where(
            PantryItem.id == item_id,
            PantryItem.household_id == household_id)
    )
    pantry_item = result.scalar_one_or_none()
    
    if pantry_item is None:
        raise HTTPException(status_code=404, detail="Pantry item not found.")

    await db.delete(pantry_item)
    await db.commit()
    return {"message": "Pantry item deleted successfully."}

