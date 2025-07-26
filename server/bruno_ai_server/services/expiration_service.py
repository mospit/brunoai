"""
Expiration management service for Bruno AI.

This service handles:
- Auto-suggesting expiration dates based on category and barcode
- Identifying items expiring within 3 days
- Managing expiration alerts and notifications
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..models.pantry import PantryItem, PantryCategory
from ..models.user import Household, User


class ExpirationService:
    """Service for managing pantry item expiration dates and alerts."""
    
    # Default expiration periods by category (in days)
    CATEGORY_EXPIRATION_DEFAULTS = {
        "dairy": 7,
        "meat": 3,
        "poultry": 3,
        "seafood": 2,
        "fruits": 5,
        "vegetables": 7,
        "bread": 5,
        "eggs": 21,
        "leftovers": 3,
        "canned_goods": 730,  # 2 years
        "dry_goods": 365,    # 1 year
        "spices": 1095,      # 3 years
        "condiments": 365,   # 1 year
        "frozen": 90,        # 3 months
        "beverages": 30,
    }
    
    # Barcode-specific expiration overrides (if we have specific product data)
    BARCODE_EXPIRATION_OVERRIDES = {
        # Example entries - in a real system, this would be a database lookup
        # "1234567890": 14,  # 2 weeks for specific product
    }

    @classmethod
    async def suggest_expiration_date(
        cls,
        item_name: str,
        category_name: Optional[str] = None,
        barcode: Optional[str] = None,
        purchase_date: Optional[date] = None
    ) -> Optional[date]:
        """
        Suggest an expiration date for a pantry item.
        
        Args:
            item_name: Name of the item
            category_name: Category of the item
            barcode: Barcode of the item (if available)
            purchase_date: Purchase date (defaults to today)
            
        Returns:
            Suggested expiration date or None if no suggestion available
        """
        if purchase_date is None:
            purchase_date = date.today()
            
        # First check barcode-specific overrides
        if barcode and barcode in cls.BARCODE_EXPIRATION_OVERRIDES:
            days_to_add = cls.BARCODE_EXPIRATION_OVERRIDES[barcode]
            return purchase_date + timedelta(days=days_to_add)
        
        # Then check category defaults
        if category_name:
            category_key = category_name.lower().replace(" ", "_")
            if category_key in cls.CATEGORY_EXPIRATION_DEFAULTS:
                days_to_add = cls.CATEGORY_EXPIRATION_DEFAULTS[category_key]
                return purchase_date + timedelta(days=days_to_add)
        
        # Try to infer category from item name
        item_name_lower = item_name.lower()
        
        # Dairy products
        if any(keyword in item_name_lower for keyword in ["milk", "cheese", "yogurt", "cream", "butter"]):
            return purchase_date + timedelta(days=cls.CATEGORY_EXPIRATION_DEFAULTS["dairy"])
        
        # Meat products
        if any(keyword in item_name_lower for keyword in ["beef", "pork", "lamb", "ground", "steak"]):
            return purchase_date + timedelta(days=cls.CATEGORY_EXPIRATION_DEFAULTS["meat"])
        
        # Poultry
        if any(keyword in item_name_lower for keyword in ["chicken", "turkey", "duck"]):
            return purchase_date + timedelta(days=cls.CATEGORY_EXPIRATION_DEFAULTS["poultry"])
        
        # Seafood
        if any(keyword in item_name_lower for keyword in ["fish", "salmon", "tuna", "shrimp", "crab"]):
            return purchase_date + timedelta(days=cls.CATEGORY_EXPIRATION_DEFAULTS["seafood"])
        
        # Fruits
        if any(keyword in item_name_lower for keyword in ["apple", "banana", "orange", "berry", "grape"]):
            return purchase_date + timedelta(days=cls.CATEGORY_EXPIRATION_DEFAULTS["fruits"])
        
        # Vegetables
        if any(keyword in item_name_lower for keyword in ["lettuce", "spinach", "carrot", "tomato", "onion"]):
            return purchase_date + timedelta(days=cls.CATEGORY_EXPIRATION_DEFAULTS["vegetables"])
        
        # Bread
        if any(keyword in item_name_lower for keyword in ["bread", "bagel", "roll", "bun"]):
            return purchase_date + timedelta(days=cls.CATEGORY_EXPIRATION_DEFAULTS["bread"])
        
        # Eggs
        if "egg" in item_name_lower:
            return purchase_date + timedelta(days=cls.CATEGORY_EXPIRATION_DEFAULTS["eggs"])
        
        # Default fallback for unknown items (1 week)
        return purchase_date + timedelta(days=7)

    @classmethod
    async def get_expiring_items(
        cls,
        db: AsyncSession,
        household_id: int,
        days_ahead: int = 3
    ) -> List[PantryItem]:
        """
        Get all items expiring within the specified number of days.
        
        Args:
            db: Database session
            household_id: ID of the household
            days_ahead: Number of days to look ahead (default: 3)
            
        Returns:
            List of pantry items expiring within the timeframe
        """
        cutoff_date = date.today() + timedelta(days=days_ahead)
        
        query = select(PantryItem).options(
            selectinload(PantryItem.category),
            selectinload(PantryItem.added_by_user)
        ).where(
            PantryItem.household_id == household_id,
            PantryItem.expiration_date.isnot(None),
            PantryItem.expiration_date <= cutoff_date,
            PantryItem.expiration_date >= date.today()  # Don't include already expired items
        ).order_by(PantryItem.expiration_date)
        
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_expired_items(
        cls,
        db: AsyncSession,
        household_id: int
    ) -> List[PantryItem]:
        """
        Get all items that have already expired.
        
        Args:
            db: Database session
            household_id: ID of the household
            
        Returns:
            List of expired pantry items
        """
        query = select(PantryItem).options(
            selectinload(PantryItem.category),
            selectinload(PantryItem.added_by_user)
        ).where(
            PantryItem.household_id == household_id,
            PantryItem.expiration_date.isnot(None),
            PantryItem.expiration_date < date.today()
        ).order_by(PantryItem.expiration_date.desc())
        
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_expiration_summary(
        cls,
        db: AsyncSession,
        household_id: int
    ) -> Dict[str, any]:
        """
        Get a summary of expiration status for a household.
        
        Args:
            db: Database session
            household_id: ID of the household
            
        Returns:
            Dictionary with expiration summary data
        """
        expiring_soon = await cls.get_expiring_items(db, household_id, 3)
        expired = await cls.get_expired_items(db, household_id)
        
        # Get items expiring in different timeframes
        expiring_today = [item for item in expiring_soon if item.expiration_date == date.today()]
        expiring_tomorrow = [item for item in expiring_soon if item.expiration_date == date.today() + timedelta(days=1)]
        expiring_this_week = await cls.get_expiring_items(db, household_id, 7)
        
        return {
            "expired_count": len(expired),
            "expiring_today_count": len(expiring_today),
            "expiring_tomorrow_count": len(expiring_tomorrow),
            "expiring_soon_count": len(expiring_soon),
            "expiring_this_week_count": len(expiring_this_week),
            "expired_items": expired,
            "expiring_today": expiring_today,
            "expiring_tomorrow": expiring_tomorrow,
            "expiring_soon": expiring_soon,
            "expiring_this_week": expiring_this_week,
            "last_updated": datetime.now().isoformat()
        }

    @classmethod 
    def categorize_expiration_urgency(cls, expiration_date: Optional[date]) -> str:
        """
        Categorize the urgency of an item's expiration.
        
        Args:
            expiration_date: The expiration date of the item
            
        Returns:
            Urgency category: "expired", "critical", "warning", "normal", "unknown"
        """
        if not expiration_date:
            return "unknown"
            
        days_until_expiration = (expiration_date - date.today()).days
        
        if days_until_expiration < 0:
            return "expired"
        elif days_until_expiration == 0:
            return "critical"  # Expires today
        elif days_until_expiration <= 3:
            return "warning"   # Expires within 3 days
        else:
            return "normal"

    @classmethod
    def get_expiration_badge_info(cls, expiration_date: Optional[date]) -> Dict[str, any]:
        """
        Get badge information for displaying expiration status.
        
        Args:
            expiration_date: The expiration date of the item
            
        Returns:
            Dictionary with badge color, text, and icon information
        """
        urgency = cls.categorize_expiration_urgency(expiration_date)
        
        badge_configs = {
            "expired": {
                "color": "#FF4444",
                "text": "EXPIRED",
                "icon": "warning",
                "text_color": "#FFFFFF"
            },
            "critical": {
                "color": "#FF8800", 
                "text": "TODAY",
                "icon": "schedule",
                "text_color": "#FFFFFF"
            },
            "warning": {
                "color": "#FFD700",
                "text": f"{(expiration_date - date.today()).days}d left",
                "icon": "schedule",
                "text_color": "#000000"
            },
            "normal": {
                "color": "#4CAF50",
                "text": f"{(expiration_date - date.today()).days}d left",
                "icon": "check_circle",
                "text_color": "#FFFFFF"
            },
            "unknown": {
                "color": "#9E9E9E",
                "text": "No date",
                "icon": "help",
                "text_color": "#FFFFFF"
            }
        }
        
        return badge_configs.get(urgency, badge_configs["unknown"])
