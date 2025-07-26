#!/usr/bin/env python3
"""
Test script for authentication tables and models.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from bruno_ai_server.models import User, RefreshToken, EmailVerification


async def test_auth_models():
    """Test authentication models functionality."""
    
    # Database URL (adjust as needed)
    DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/bruno_ai_v2"
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as session:
        try:
            # Create a test user
            user = User(
                email="test@example.com",
                full_name="Test User",
                password_hash="$2b$12$LQv3c1yqBWVHxkd0LQ1lqe.0x4v7lc.Lz0o2d1e0f3g4h5i6j7k8l9m",
                status="active",
                is_verified=True
            )
            
            session.add(user)
            await session.flush()  # Get the user ID
            
            print(f"Created user: {user}")
            
            # Create a refresh token
            refresh_token = RefreshToken(
                user_id=user.id,
                token="test_refresh_token_abc123",
                expires_at=datetime.utcnow() + timedelta(days=30),
                device_info={"device": "test_device", "ip": "127.0.0.1"}
            )
            
            session.add(refresh_token)
            
            print(f"Created refresh token: {refresh_token}")
            print(f"Token is valid: {refresh_token.is_valid}")
            print(f"Token is expired: {refresh_token.is_expired}")
            
            # Create an email verification
            email_verification = EmailVerification(
                user_id=user.id,
                verification_token="verify_token_xyz789",
                email=user.email,
                token_type="email_verify",
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            
            session.add(email_verification)
            
            print(f"Created email verification: {email_verification}")
            print(f"Verification is valid: {email_verification.is_valid}")
            print(f"Verification is expired: {email_verification.is_expired}")
            
            await session.commit()
            
            # Test relationships
            print(f"User refresh tokens: {len(user.refresh_tokens)}")
            print(f"User email verifications: {len(user.email_verifications)}")
            
            # Test verification methods
            print(f"Before marking as verified: {email_verification.is_verified}")
            email_verification.mark_as_verified()
            print(f"After marking as verified: {email_verification.is_verified}")
            
            # Test increment attempts
            print(f"Attempts before increment: {email_verification.attempts}")
            email_verification.increment_attempts()
            print(f"Attempts after increment: {email_verification.attempts}")
            
            await session.commit()
            print("✅ All authentication model tests passed!")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
    
    await engine.dispose()


if __name__ == "__main__":
    print("Testing authentication models...")
    asyncio.run(test_auth_models())
