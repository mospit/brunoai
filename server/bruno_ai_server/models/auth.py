"""
Authentication-related database models.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class RefreshToken(Base, TimestampMixin):
    """Refresh token model for JWT token management."""

    __tablename__ = "refresh_tokens"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(500), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    device_info = Column(JSONB, default=dict)

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

    # Constraints
    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="expires_after_created"),
    )

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"

    @property
    def is_expired(self):
        """Check if the token is expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self):
        """Check if the token is valid (not revoked and not expired)."""
        return not self.is_revoked and not self.is_expired


class EmailVerification(Base, TimestampMixin):
    """Email verification token model for account verification and password resets."""

    __tablename__ = "email_verifications"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    verification_token = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=False)
    token_type = Column(String(50), nullable=False)  # 'email_verify' or 'password_reset'
    requested_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    attempts = Column(Integer, default=0, nullable=False)

    # Relationships
    user = relationship("User", back_populates="email_verifications")

    # Constraints
    __table_args__ = (
        CheckConstraint("token_type IN ('email_verify', 'password_reset')", name="valid_token_type"),
        CheckConstraint("attempts >= 0", name="non_negative_attempts"),
        CheckConstraint("expires_at > requested_at", name="expires_after_requested"),
    )

    def __repr__(self):
        return f"<EmailVerification(id={self.id}, user_id={self.user_id}, token_type='{self.token_type}')>"

    @property
    def is_expired(self):
        """Check if the verification token is expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_verified(self):
        """Check if the verification has been completed."""
        return self.verified_at is not None

    @property
    def is_valid(self):
        """Check if the token is valid (not expired and not already verified)."""
        return not self.is_expired and not self.is_verified

    def mark_as_verified(self):
        """Mark the verification as completed."""
        self.verified_at = datetime.utcnow()

    def increment_attempts(self):
        """Increment the verification attempts counter."""
        self.attempts += 1
