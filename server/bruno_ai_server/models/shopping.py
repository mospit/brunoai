"""
Shopping and order-related database models.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class ShoppingList(Base, TimestampMixin):
    """Collaborative shopping lists for households."""

    __tablename__ = "shopping_lists"

    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Status tracking
    status = Column(String(50), default="active")  # active, completed, archived
    is_shared = Column(Boolean, default=True)

    # Relationships
    household_id = Column(UUID(as_uuid=True), ForeignKey("households.id"), nullable=False)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    household = relationship("Household")
    created_by_user = relationship("User")
    items = relationship("ShoppingListItem", back_populates="shopping_list")
    orders = relationship("Order", back_populates="shopping_list")

    # Metadata for AI suggestions, preferences
    list_metadata = Column(JSONB, default=dict)

    def __repr__(self):
        return f"<ShoppingList(id={self.id}, name='{self.name}', status='{self.status}')>"


class ShoppingListItem(Base, TimestampMixin):
    """Individual items in a shopping list."""

    __tablename__ = "shopping_list_items"

    name = Column(String(255), nullable=False)
    quantity = Column(Float, default=1.0)
    unit = Column(String(50), default="piece")
    notes = Column(Text)

    # Status tracking
    is_purchased = Column(Boolean, default=False)
    priority = Column(String(20), default="medium")  # high, medium, low

    # Price estimation
    estimated_price = Column(Float)
    actual_price = Column(Float)

    # Relationships
    shopping_list_id = Column(UUID(as_uuid=True), ForeignKey("shopping_lists.id"), nullable=False)
    added_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    shopping_list = relationship("ShoppingList", back_populates="items")
    added_by_user = relationship("User")

    # Recipe connection (if item comes from a recipe)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipes.id"))
    recipe = relationship("Recipe")

    def __repr__(self):
        return f"<ShoppingListItem(id={self.id}, name='{self.name}', quantity={self.quantity}, purchased={self.is_purchased})>"


class Order(Base, TimestampMixin):
    """Orders placed through third-party services like Instacart."""

    __tablename__ = "orders"

    # External service information
    external_order_id = Column(String(100), unique=True, index=True)  # Instacart order ID
    service_provider = Column(String(50), default="instacart")  # instacart, amazon_fresh, etc.

    # Order details
    total_amount = Column(Float)
    tax_amount = Column(Float)
    delivery_fee = Column(Float)
    tip_amount = Column(Float)

    # Status tracking
    status = Column(String(50))  # pending, confirmed, in_progress, delivered, cancelled
    estimated_delivery = Column(DateTime)
    actual_delivery = Column(DateTime)

    # Location and delivery
    delivery_address = Column(JSONB)  # Store address as JSON
    delivery_instructions = Column(Text)

    # Relationships
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    household_id = Column(UUID(as_uuid=True), ForeignKey("households.id"), nullable=False)
    shopping_list_id = Column(UUID(as_uuid=True), ForeignKey("shopping_lists.id"))

    user = relationship("User")
    household = relationship("Household")
    shopping_list = relationship("ShoppingList", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

    # Additional tracking and metadata
    affiliate_tracking_id = Column(String(100))  # For commission tracking
    order_metadata = Column(JSONB, default=dict)  # Store API responses, tracking info

    def __repr__(self):
        return f"<Order(id={self.id}, external_id='{self.external_order_id}', status='{self.status}', total={self.total_amount})>"


class OrderItem(Base, TimestampMixin):
    """Individual items in an order."""

    __tablename__ = "order_items"

    name = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50))
    unit_price = Column(Float)
    total_price = Column(Float)

    # Product identification
    barcode = Column(String(50))
    brand = Column(String(100))
    size = Column(String(50))

    # Relationships
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    shopping_list_item_id = Column(UUID(as_uuid=True), ForeignKey("shopping_list_items.id"))

    order = relationship("Order", back_populates="items")
    shopping_list_item = relationship("ShoppingListItem")

    # Store external service item data
    external_item_data = Column(JSONB, default=dict)

    def __repr__(self):
        return f"<OrderItem(id={self.id}, name='{self.name}', quantity={self.quantity}, price={self.total_price})>"
