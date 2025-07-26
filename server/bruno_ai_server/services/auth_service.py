"""
Authentication service layer for Bruno AI Server.
"""

import secrets
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from passlib.context import CryptContext
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.auth import EmailVerification, RefreshToken
from ..models.user import User
from ..validation import validate_email_format, validate_password_strength, validate_name, ValidationError


class AuthenticationService:
    """Service class for authentication operations."""
    
    def __init__(self):
        # Use bcrypt with appropriate rounds for security vs performance balance
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12  # Good balance between security and performance
        )
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from database
            
        Returns:
            bool: True if password matches
        """
        if not plain_password or not hashed_password:
            return False
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def generate_verification_token(self) -> str:
        """
        Generate a secure verification token.
        
        Returns:
            str: Random verification token
        """
        return secrets.token_urlsafe(32)
    
    async def create_user(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        name: str
    ) -> User:
        """
        Create a new user with validation and password hashing.
        
        Args:
            db: Database session
            email: User email (will be validated)
            password: Plain text password (will be hashed)
            name: User's name
            
        Returns:
            User: Created user object
            
        Raises:
            ValidationError: If validation fails
            ValueError: If user already exists
        """
        # Validate email format
        validate_email_format(email)
        email = email.strip().lower()
        
        # Validate password strength
        password_result = validate_password_strength(password)
        if not password_result.is_valid:
            raise ValidationError("; ".join(password_result.errors), "password")
        
        # Check if user already exists
        existing_user = await self.get_user_by_email(db, email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Hash password
        hashed_password = self.hash_password(password)
        
        # Create user
        user = User(
            email=email,
            name=name.strip(),
            is_active=True,
            is_verified=False,
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user
    
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            db: Database session
            email: Email address
            
        Returns:
            Optional[User]: User object if found
        """
        if not email:
            return None
        
        email = email.strip().lower()
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Optional[User]: User object if found
        """
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def authenticate_user(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        request=None
    ) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            db: Database session
            email: User email
            password: Plain text password (NEVER logged)
            request: Optional request object for security logging
            
        Returns:
            Optional[User]: User object if authentication succeeds
        """
        if not email or not password:
            if request:
                from ..services.security_service import security_service
                security_service.logger.log_auth_attempt(
                    request, email or "unknown", False, "missing_credentials"
                )
            return None
        
        user = await self.get_user_by_email(db, email)
        if not user:
            if request:
                from ..services.security_service import security_service
                security_service.logger.log_auth_attempt(
                    request, email, False, "user_not_found"
                )
            return None
        
        # Password authentication is no longer supported after schema migration
        # TODO: Implement Firebase authentication
        if request:
            from ..services.security_service import security_service
            security_service.logger.log_auth_attempt(
                request, email, False, "password_auth_disabled", str(user.id)
            )
        return None
    
    async def create_email_verification(
        self,
        db: AsyncSession,
        user_id: int,
        email: str,
        token_type: str = "email_verify",
        expires_hours: int = 24
    ) -> EmailVerification:
        """
        Create an email verification token.
        
        Args:
            db: Database session
            user_id: User ID
            email: Email address
            token_type: Type of verification ('email_verify' or 'password_reset')
            expires_hours: Token expiration in hours
            
        Returns:
            EmailVerification: Created verification object
        """
        # Deactivate any existing verification tokens for this user and type
        await db.execute(
            delete(EmailVerification).where(
                EmailVerification.user_id == user_id,
                EmailVerification.token_type == token_type,
                EmailVerification.verified_at.is_(None)
            )
        )
        
        verification = EmailVerification(
            user_id=user_id,
            verification_token=self.generate_verification_token(),
            email=email.strip().lower(),
            token_type=token_type,
            expires_at=datetime.utcnow() + timedelta(hours=expires_hours)
        )
        
        db.add(verification)
        await db.commit()
        await db.refresh(verification)
        
        return verification
    
    async def verify_email_token(
        self,
        db: AsyncSession,
        token: str,
        token_type: str = "email_verify"
    ) -> Optional[Tuple[User, EmailVerification]]:
        """
        Verify an email verification token.
        
        Args:
            db: Database session
            token: Verification token
            token_type: Type of verification
            
        Returns:
            Optional[Tuple[User, EmailVerification]]: User and verification objects if valid
        """
        if not token:
            return None
        
        result = await db.execute(
            select(EmailVerification)
            .options(selectinload(EmailVerification.user))
            .where(
                EmailVerification.verification_token == token,
                EmailVerification.token_type == token_type,
                EmailVerification.verified_at.is_(None)
            )
        )
        verification = result.scalar_one_or_none()
        
        if not verification or verification.is_expired:
            return None
        
        # Mark as verified
        verification.mark_as_verified()
        
        # If email verification, activate user
        if token_type == "email_verify":
            verification.user.is_verified = True
        
        await db.commit()
        
        return verification.user, verification
    
    async def create_refresh_token(
        self,
        db: AsyncSession,
        user_id: int,
        token: str,
        device_info: Optional[Dict] = None,
        expires_days: int = 7
    ) -> RefreshToken:
        """
        Create a refresh token record.
        
        Args:
            db: Database session
            user_id: User ID
            token: JWT refresh token
            device_info: Optional device information
            expires_days: Token expiration in days
            
        Returns:
            RefreshToken: Created refresh token object
        """
        refresh_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(days=expires_days),
            device_info=device_info or {}
        )
        
        db.add(refresh_token)
        await db.commit()
        await db.refresh(refresh_token)
        
        return refresh_token
    
    async def get_refresh_token(
        self,
        db: AsyncSession,
        token: str
    ) -> Optional[RefreshToken]:
        """
        Get refresh token by token value.
        
        Args:
            db: Database session
            token: Refresh token value
            
        Returns:
            Optional[RefreshToken]: Refresh token object if found and valid
        """
        result = await db.execute(
            select(RefreshToken)
            .options(selectinload(RefreshToken.user))
            .where(
                RefreshToken.token == token,
                RefreshToken.is_revoked == False
            )
        )
        refresh_token = result.scalar_one_or_none()
        
        if not refresh_token or refresh_token.is_expired:
            return None
        
        return refresh_token
    
    async def revoke_refresh_token(
        self,
        db: AsyncSession,
        token: str
    ) -> bool:
        """
        Revoke a refresh token.
        
        Args:
            db: Database session
            token: Refresh token to revoke
            
        Returns:
            bool: True if token was revoked
        """
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token == token)
        )
        refresh_token = result.scalar_one_or_none()
        
        if not refresh_token:
            return False
        
        refresh_token.is_revoked = True
        await db.commit()
        
        return True
    
    async def revoke_all_user_tokens(
        self,
        db: AsyncSession,
        user_id: int
    ) -> int:
        """
        Revoke all refresh tokens for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            int: Number of tokens revoked
        """
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False
            )
        )
        tokens = result.scalars().all()
        
        count = 0
        for token in tokens:
            token.is_revoked = True
            count += 1
        
        if count > 0:
            await db.commit()
        
        return count
    
    async def cleanup_expired_tokens(self, db: AsyncSession) -> Dict[str, int]:
        """
        Clean up expired tokens and verifications.
        
        Args:
            db: Database session
            
        Returns:
            Dict[str, int]: Cleanup statistics
        """
        now = datetime.utcnow()
        
        # Clean up expired refresh tokens
        refresh_result = await db.execute(
            delete(RefreshToken).where(RefreshToken.expires_at < now)
        )
        
        # Clean up expired email verifications
        verification_result = await db.execute(
            delete(EmailVerification).where(EmailVerification.expires_at < now)
        )
        
        await db.commit()
        
        return {
            "refresh_tokens_deleted": refresh_result.rowcount,
            "email_verifications_deleted": verification_result.rowcount
        }
    
    async def change_password(
        self,
        db: AsyncSession,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password with current password verification.
        
        Args:
            db: Database session
            user_id: User ID
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            bool: True if password was changed successfully
            
        Raises:
            ValidationError: If new password is invalid
            ValueError: If current password is incorrect
        """
        user = await self.get_user_by_id(db, user_id)
        if not user:
            return False
        
        # Verify current password
        if not self.verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")
        
        # Validate new password strength
        password_result = validate_password_strength(new_password)
        if not password_result.is_valid:
            raise ValidationError("; ".join(password_result.errors), "new_password")
        
        # Update password
        user.password_hash = self.hash_password(new_password)
        await db.commit()
        
        # Revoke all existing refresh tokens for security
        await self.revoke_all_user_tokens(db, user_id)
        
        return True
    
    async def reset_password(
        self,
        db: AsyncSession,
        token: str,
        new_password: str
    ) -> bool:
        """
        Reset password using a password reset token.
        
        Args:
            db: Database session
            token: Password reset token
            new_password: New password
            
        Returns:
            bool: True if password was reset successfully
            
        Raises:
            ValidationError: If new password is invalid
            ValueError: If token is invalid or expired
        """
        # Verify reset token
        result = await self.verify_email_token(db, token, "password_reset")
        if not result:
            raise ValueError("Invalid or expired reset token")
        
        user, verification = result
        
        # Validate new password strength
        password_result = validate_password_strength(new_password)
        if not password_result.is_valid:
            raise ValidationError("; ".join(password_result.errors), "new_password")
        
        # Update password
        user.password_hash = self.hash_password(new_password)
        await db.commit()
        
        # Revoke all existing refresh tokens for security
        await self.revoke_all_user_tokens(db, user.id)
        
        return True


# Global service instance
auth_service = AuthenticationService()
