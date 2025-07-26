"""
Expiration management API routes for Bruno AI.
"""

from datetime import date, datetime, timedelta
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_active_user
from ..database import get_async_session
from ..models.user import User
from ..routes.pantry import get_user_household_id
from ..schemas import PantryItemResponse
from ..services.expiration_service import ExpirationService

# Define the router
router = APIRouter(prefix="/expiration", tags=["expiration"])


@router.get("/suggest", response_model=Dict[str, any])
async def suggest_expiration_date(
    item_name: str = Query(..., description="Name of the item"),
    category_name: str = Query(None, description="Category of the item"),
    barcode: str = Query(None, description="Barcode of the item"),
    purchase_date: date = Query(None, description="Purchase date (defaults to today)")
):
    """Get suggested expiration date for an item."""
    suggested_date = await ExpirationService.suggest_expiration_date(
        item_name=item_name,
        category_name=category_name,
        barcode=barcode,
        purchase_date=purchase_date
    )
    
    return {
        "item_name": item_name,
        "category_name": category_name,
        "barcode": barcode,
        "purchase_date": purchase_date or date.today(),
        "suggested_expiration_date": suggested_date,
        "days_until_expiration": (suggested_date - (purchase_date or date.today())).days if suggested_date else None
    }


@router.get("/expiring", response_model=List[PantryItemResponse])
async def get_expiring_items(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
    days_ahead: int = Query(3, description="Number of days to look ahead", ge=1, le=30)
):
    """Get all items expiring within the specified number of days."""
    household_id = await get_user_household_id(current_user, db)
    if not household_id:
        raise HTTPException(status_code=400, detail="User is not a member of any household")
    
    expiring_items = await ExpirationService.get_expiring_items(
        db=db,
        household_id=household_id,
        days_ahead=days_ahead
    )
    
    return expiring_items


@router.get("/expired", response_model=List[PantryItemResponse])
async def get_expired_items(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get all items that have already expired."""
    household_id = await get_user_household_id(current_user, db)
    if not household_id:
        raise HTTPException(status_code=400, detail="User is not a member of any household")
    
    expired_items = await ExpirationService.get_expired_items(
        db=db,
        household_id=household_id
    )
    
    return expired_items


@router.get("/summary", response_model=Dict[str, any])
async def get_expiration_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get a comprehensive summary of expiration status for the household."""
    household_id = await get_user_household_id(current_user, db)
    if not household_id:
        raise HTTPException(status_code=400, detail="User is not a member of any household")
    
    summary = await ExpirationService.get_expiration_summary(
        db=db,
        household_id=household_id
    )
    
    return summary


@router.get("/badge-info", response_model=Dict[str, any])
async def get_expiration_badge_info(
    expiration_date: date = Query(..., description="Expiration date of the item")
):
    """Get badge information for displaying expiration status."""
    badge_info = ExpirationService.get_expiration_badge_info(expiration_date)
    
    return {
        "expiration_date": expiration_date,
        "urgency": ExpirationService.categorize_expiration_urgency(expiration_date),
        "badge": badge_info
    }


@router.get("/alerts", response_model=Dict[str, any])
async def get_expiration_alerts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get expiration alerts for the current user's household."""
    household_id = await get_user_household_id(current_user, db)
    if not household_id:
        raise HTTPException(status_code=400, detail="User is not a member of any household")
    
    # Get items in different urgency categories
    expiring_today = await ExpirationService.get_expiring_items(db, household_id, 0)
    expiring_tomorrow = await ExpirationService.get_expiring_items(db, household_id, 1)  
    expiring_soon = await ExpirationService.get_expiring_items(db, household_id, 3)
    expired = await ExpirationService.get_expired_items(db, household_id)
    
    # Filter to get only today and tomorrow from the expiring_soon list
    expiring_today_filtered = [item for item in expiring_soon if item.expiration_date == date.today()]
    expiring_tomorrow_filtered = [item for item in expiring_soon if item.expiration_date == date.today() + timedelta(days=1)]
    
    alerts = []
    
    # Critical alerts (expired items)
    if expired:
        alerts.append({
            "type": "critical",
            "title": f"{len(expired)} item{'s' if len(expired) != 1 else ''} expired",
            "message": f"You have {len(expired)} expired item{'s' if len(expired) != 1 else ''} in your pantry",
            "items": expired,
            "priority": 1
        })
    
    # High priority alerts (expiring today)  
    if expiring_today_filtered:
        alerts.append({
            "type": "high",
            "title": f"{len(expiring_today_filtered)} item{'s' if len(expiring_today_filtered) != 1 else ''} expiring today",
            "message": f"Use {len(expiring_today_filtered)} item{'s' if len(expiring_today_filtered) != 1 else ''} today before {'they expire' if len(expiring_today_filtered) != 1 else 'it expires'}",
            "items": expiring_today_filtered,
            "priority": 2
        })
    
    # Medium priority alerts (expiring tomorrow)
    if expiring_tomorrow_filtered:
        alerts.append({
            "type": "medium", 
            "title": f"{len(expiring_tomorrow_filtered)} item{'s' if len(expiring_tomorrow_filtered) != 1 else ''} expiring tomorrow",
            "message": f"Plan to use {len(expiring_tomorrow_filtered)} item{'s' if len(expiring_tomorrow_filtered) != 1 else ''} tomorrow",
            "items": expiring_tomorrow_filtered,
            "priority": 3
        })
    
    # Low priority alerts (expiring within 3 days)
    remaining_expiring_soon = [item for item in expiring_soon if item not in expiring_today_filtered and item not in expiring_tomorrow_filtered]
    if remaining_expiring_soon:
        alerts.append({
            "type": "low",
            "title": f"{len(remaining_expiring_soon)} item{'s' if len(remaining_expiring_soon) != 1 else ''} expiring soon",
            "message": f"{len(remaining_expiring_soon)} item{'s' if len(remaining_expiring_soon) != 1 else ''} will expire within 3 days",
            "items": remaining_expiring_soon,
            "priority": 4
        })
    
    # Sort alerts by priority
    alerts.sort(key=lambda x: x["priority"])
    
    return {
        "alerts": alerts,
        "total_alerts": len(alerts),
        "has_critical_alerts": any(alert["type"] == "critical" for alert in alerts),
        "has_high_priority_alerts": any(alert["type"] == "high" for alert in alerts),
        "generated_at": datetime.now().isoformat()
    }
