"""
API routes for Bruno AI Server.
"""

from .auth import router as auth_router
from .pantry import router as pantry_router
from .voice import router as voice_router
from .categories import router as categories_router

__all__ = ["auth_router", "pantry_router", "voice_router", "categories_router"]
