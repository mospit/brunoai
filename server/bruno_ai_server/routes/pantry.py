"""
Pantry router for handling pantry items.
"""


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import date, timedelta

from ..auth import get_current_active_user
from ..database import get_async_session
from ..models.pantry import PantryCategory, PantryItem
from ..models.user import HouseholdMember, User
from ..schemas import PantryItemCreate, PantryItemResponse, PantryItemUpdate
from ..services.expiration_service import ExpirationService

# Define the router
router = APIRouter(prefix="/pantry/items", tags=["pantry"])


async def get_user_household_id(user: User, db: AsyncSession) -> int | None:
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
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    category: Optional[str] = Query(None, description="Filter by category name"),
    search: Optional[str] = Query(None, description="Search by keyword"),
    expiration_status: Optional[str] = Query(None, description="Filter by expiration status: expired, expiring_soon, fresh"),
    sort_by: Optional[str] = Query("name", description="Sort by: name, expiration_date, created_at"),
    sort_order: Optional[str] = Query("asc", description="Sort order: asc, desc")
):
    """Retrieve all pantry items for the current user's household with filtering and sorting."""
    household_id = await get_user_household_id(current_user, db)
    if not household_id:
        raise HTTPException(status_code=400, detail="User is not a member of any household")

    query = select(PantryItem).where(PantryItem.household_id == household_id)

    # Filter by category ID (takes precedence over category name)
    if category_id:
        query = query.where(PantryItem.category_id == category_id)
    elif category:
        query = query.join(PantryCategory).where(PantryCategory.name == category)
    
    # Search functionality
    if search:
        query = query.where(PantryItem.name.ilike(f"%{search}%"))
    
    # Filter by expiration status
    if expiration_status:
        today = date.today()
        if expiration_status == "expired":
            query = query.where(PantryItem.expiration_date < today)
        elif expiration_status == "expiring_soon":
            three_days_from_now = today + timedelta(days=3)
            query = query.where(
                PantryItem.expiration_date >= today,
                PantryItem.expiration_date <= three_days_from_now
            )
        elif expiration_status == "fresh":
            three_days_from_now = today + timedelta(days=3)
            query = query.where(PantryItem.expiration_date > three_days_from_now)
    
    # Sorting
    if sort_by == "expiration_date":
        sort_column = PantryItem.expiration_date
    elif sort_by == "created_at":
        sort_column = PantryItem.created_at
    else:  # default to name
        sort_column = PantryItem.name
    
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    result = await db.execute(query.options(
        selectinload(PantryItem.category), 
        selectinload(PantryItem.added_by_user)
    ))
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

    # Get category name if category_id is provided
    category_name = None
    if pantry_item_data.category_id:
        result = await db.execute(
            select(PantryCategory).where(PantryCategory.id == pantry_item_data.category_id)
        )
        category = result.scalar_one_or_none()
        if category:
            category_name = category.name
    
    # Auto-suggest expiration date if not provided
    expiration_date = pantry_item_data.expiration_date
    if not expiration_date:
        suggested_date = await ExpirationService.suggest_expiration_date(
            item_name=pantry_item_data.name,
            category_name=category_name,
            barcode=pantry_item_data.barcode
        )
        expiration_date = suggested_date

    pantry_item = PantryItem(
        **pantry_item_data.dict(exclude={'expiration_date'}),
        expiration_date=expiration_date,
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


@router.patch("/{item_id}/increment", response_model=PantryItemResponse)
async def increment_pantry_item_quantity(
    item_id: int,
    amount: float = Query(1.0, description="Amount to increment by"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Increment the quantity of a pantry item."""
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
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Increment amount must be positive")

    # Update quantity
    pantry_item.quantity += amount
    await db.commit()
    await db.refresh(pantry_item)
    return pantry_item


@router.patch("/{item_id}/decrement", response_model=PantryItemResponse)
async def decrement_pantry_item_quantity(
    item_id: int,
    amount: float = Query(1.0, description="Amount to decrement by"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Decrement the quantity of a pantry item. If quantity reaches 0, item can be optionally deleted."""
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
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Decrement amount must be positive")

    # Update quantity, ensuring it doesn't go below 0
    new_quantity = max(0, pantry_item.quantity - amount)
    pantry_item.quantity = new_quantity
    
    await db.commit()
    await db.refresh(pantry_item)
    return pantry_item


@router.patch("/{item_id}/set-quantity", response_model=PantryItemResponse)
async def set_pantry_item_quantity(
    item_id: int,
    quantity: float = Query(..., description="New quantity to set"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Set the exact quantity of a pantry item."""
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
    
    if quantity < 0:
        raise HTTPException(status_code=400, detail="Quantity cannot be negative")

    # Update quantity
    pantry_item.quantity = quantity
    await db.commit()
    await db.refresh(pantry_item)
    return pantry_item

