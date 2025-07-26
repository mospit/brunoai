"""
Pydantic schemas for API request/response models.
"""

from datetime import date, datetime
from typing import Any, List, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, validator


# Authentication schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    name: str


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
    id: UUID
    firebase_uid: Optional[str] = None
    is_active: bool
    is_verified: bool
    dietary_preferences: dict[str, Any] = {}
    voice_settings: dict[str, Any] = {}
    notification_preferences: dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token data."""
    user_id: UUID | None = None


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
    admin_user_id: int
    settings: dict[str, Any] = {}
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
    description: str | None = None
    icon: str | None = None
    color: str | None = None

    class Config:
        from_attributes = True


class PantryItemBase(BaseModel):
    """Base pantry item schema."""
    name: str
    quantity: float = 1.0
    unit: str = "piece"
    location: str | None = None
    notes: str | None = None


class PantryItemCreate(PantryItemBase):
    """Schema for pantry item creation."""
    barcode: str | None = None
    expiration_date: date | None = None
    category_id: int | None = None


class PantryItemUpdate(BaseModel):
    """Schema for pantry item update."""
    name: str | None = None
    quantity: float | None = None
    unit: str | None = None
    location: str | None = None
    notes: str | None = None
    expiration_date: date | None = None
    category_id: int | None = None


class PantryItemQuantityAdjustment(BaseModel):
    """Schema for quantity adjustment requests."""
    amount: float
    item_name: str | None = None  # For voice commands that specify item by name
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v


class PantryItemSetQuantity(BaseModel):
    """Schema for setting exact quantity."""
    quantity: float
    item_name: str | None = None  # For voice commands that specify item by name
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 0:
            raise ValueError('Quantity cannot be negative')
        return v


class PantryItemResponse(PantryItemBase):
    """Schema for pantry item response."""
    id: int
    barcode: str | None = None
    expiration_date: date | None = None
    purchase_date: date | None = None
    household_id: int
    category_id: int | None = None
    added_by_user_id: int
    item_metadata: dict[str, Any] = {}
    created_at: datetime

    # Relationships
    category: PantryCategoryResponse | None = None
    added_by_user: UserResponse

    class Config:
        from_attributes = True


# Voice processing schemas
class VoiceTranscriptionRequest(BaseModel):
    """Schema for voice transcription request metadata."""
    language: str | None = None
    enhance_food_terms: bool = True


class VoiceTranscriptionResponse(BaseModel):
    """Schema for voice transcription response."""
    text: str
    confidence: float
    language_detected: str | None = None
    processing_time_ms: int
    audio_duration_ms: int


class PantryActionEntity(BaseModel):
    """Schema for parsed pantry action entity."""
    name: str
    quantity: float | None = None
    unit: str | None = None
    location: str | None = None
    expiration_date: date | None = None
    confidence: float = 1.0


class PantryActionCommand(BaseModel):
    """Schema for parsed pantry action command."""
    action: str  # add, update, delete, list, search, check
    entities: List[PantryActionEntity]
    raw_text: str
    confidence: float
    errors: List[str] | None = None
    metadata: Dict[str, Any] | None = None


class VoiceCommandResponse(BaseModel):
    """Schema for complete voice command processing response."""
    transcription: VoiceTranscriptionResponse
    command: PantryActionCommand
    success: bool
    message: str | None = None


# TTS schemas
class TTSVoiceResponse(BaseModel):
    """Schema for TTS voice information."""
    id: str
    name: str
    language: str
    gender: str
    accent: str | None = None
    provider: str | None = None
    naturalness_score: float = 0.0


class TTSSynthesisRequest(BaseModel):
    """Schema for TTS synthesis request."""
    text: str
    voice_id: str | None = None
    language: str = "en"
    speed: float = 1.0
    pitch: float = 0.0
    accent: str | None = None
    ssml: bool = False
    optimize_for_kitchen: bool = True
    
    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty')
        if len(v) > 5000:
            raise ValueError('Text too long (max 5000 characters)')
        return v
    
    @validator('speed')
    def validate_speed(cls, v):
        if not 0.25 <= v <= 4.0:
            raise ValueError('Speed must be between 0.25 and 4.0')
        return v
    
    @validator('pitch')
    def validate_pitch(cls, v):
        if not -20.0 <= v <= 20.0:
            raise ValueError('Pitch must be between -20.0 and 20.0')
        return v


class TTSSynthesisResponse(BaseModel):
    """Schema for TTS synthesis response."""
    audio_data: str  # Base64 encoded audio
    audio_format: str
    duration_ms: int
    voice_used: TTSVoiceResponse
    provider: str
    processing_time_ms: int
    cache_hit: bool = False


class TTSProviderStatus(BaseModel):
    """Schema for TTS provider status."""
    status: str
    latency_score: int | None = None
    naturalness_score: int | None = None
    error: str | None = None
    note: str | None = None


class TTSHealthResponse(BaseModel):
    """Schema for TTS service health response."""
    service: str
    status: str
    providers: Dict[str, TTSProviderStatus]
    preferred_provider: str | None = None
    cache_size: int
    supported_languages: List[str]
    supported_accents: List[str]
    message: str | None = None


# Recipe schemas
class RecipeBase(BaseModel):
    """Base recipe schema."""
    title: str
    description: str | None = None
    instructions: str


class RecipeCreate(RecipeBase):
    """Schema for recipe creation."""
    prep_time_minutes: int | None = None
    cook_time_minutes: int | None = None
    servings: int = 4
    difficulty_level: str | None = None
    tags: list = []
    cuisine_type: str | None = None


class RecipeResponse(RecipeBase):
    """Schema for recipe response."""
    id: int
    prep_time_minutes: int | None = None
    cook_time_minutes: int | None = None
    servings: int
    difficulty_level: str | None = None
    nutrition_info: dict[str, Any] = {}
    tags: list = []
    cuisine_type: str | None = None
    external_source: str | None = None
    external_id: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
