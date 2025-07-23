"""
Pydantic schemas for API request/response models.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, validator


# Authentication schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool
    is_verified: bool
    dietary_preferences: Dict[str, Any] = {}
    voice_settings: Dict[str, Any] = {}
    notification_preferences: Dict[str, Any] = {}
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token data."""
    user_id: Optional[int] = None


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


# Household schemas
class HouseholdBase(BaseModel):
    """Base household schema."""
    name: str


class HouseholdCreate(HouseholdBase):
    """Schema for household creation."""
    pass


class HouseholdResponse(HouseholdBase):
    """Schema for household response."""
    id: int
    invite_code: str
    owner_id: int
    settings: Dict[str, Any] = {}
    created_at: datetime
    
    class Config:
        from_attributes = True


class HouseholdMemberResponse(BaseModel):
    """Schema for household member response."""
    id: int
    user_id: int
    household_id: int
    role: str
    joined_at: datetime
    user: UserResponse
    
    class Config:
        from_attributes = True


# Pantry schemas
class PantryCategoryResponse(BaseModel):
    """Schema for pantry category response."""
    id: int
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    
    class Config:
        from_attributes = True


class PantryItemBase(BaseModel):
    """Base pantry item schema."""
    name: str
    quantity: float = 1.0
    unit: str = "piece"
    location: Optional[str] = None
    notes: Optional[str] = None


class PantryItemCreate(PantryItemBase):
    """Schema for pantry item creation."""
    barcode: Optional[str] = None
    expiration_date: Optional[date] = None
    category_id: Optional[int] = None


class PantryItemUpdate(BaseModel):
    """Schema for pantry item update."""
    name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    expiration_date: Optional[date] = None
    category_id: Optional[int] = None


class PantryItemResponse(PantryItemBase):
    """Schema for pantry item response."""
    id: int
    barcode: Optional[str] = None
    expiration_date: Optional[date] = None
    purchase_date: Optional[date] = None
    household_id: int
    category_id: Optional[int] = None
    added_by_user_id: int
    item_metadata: Dict[str, Any] = {}
    created_at: datetime
    
    # Relationships
    category: Optional[PantryCategoryResponse] = None
    added_by_user: UserResponse
    
    class Config:
        from_attributes = True


# Recipe schemas
class RecipeBase(BaseModel):
    """Base recipe schema."""
    title: str
    description: Optional[str] = None
    instructions: str


class RecipeCreate(RecipeBase):
    """Schema for recipe creation."""
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    servings: int = 4
    difficulty_level: Optional[str] = None
    tags: list = []
    cuisine_type: Optional[str] = None


class RecipeResponse(RecipeBase):
    """Schema for recipe response."""
    id: int
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    servings: int
    difficulty_level: Optional[str] = None
    nutrition_info: Dict[str, Any] = {}
    tags: list = []
    cuisine_type: Optional[str] = None
    external_source: Optional[str] = None
    external_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
