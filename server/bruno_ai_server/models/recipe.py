"""
Recipe-related database models.
"""

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Recipe(Base, TimestampMixin):
    """Recipe model for meal suggestions."""

    __tablename__ = "recipes"

    title = Column(String(255), nullable=False)
    description = Column(Text)
    instructions = Column(Text, nullable=False)

    # Recipe metadata
    prep_time_minutes = Column(Integer)  # Preparation time in minutes
    cook_time_minutes = Column(Integer)  # Cooking time in minutes
    servings = Column(Integer, default=4)
    difficulty_level = Column(String(20))  # easy, medium, hard

    # Nutrition information stored as JSON
    nutrition_info = Column(JSONB, default=dict)

    # Recipe tags and categories
    tags = Column(JSONB, default=list)  # ["vegetarian", "quick", "healthy"]
    cuisine_type = Column(String(100))

    # External references
    external_source = Column(String(255))  # Source URL or API reference
    external_id = Column(String(100))  # External system ID

    # Relationships
    ingredients = relationship("RecipeIngredient", back_populates="recipe")
    user_favorites = relationship("UserFavorite", back_populates="recipe")

    def __repr__(self):
        return f"<Recipe(id={self.id}, title='{self.title}', servings={self.servings})>"


class RecipeIngredient(Base, TimestampMixin):
    """Ingredients required for a recipe."""

    __tablename__ = "recipe_ingredients"

    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=False)
    name = Column(String(255), nullable=False)
    quantity = Column(Float)
    unit = Column(String(50))
    notes = Column(String(255))  # "chopped", "to taste", etc.
    is_optional = Column(String(10), default="false")  # For optional ingredients

    # Relationships
    recipe = relationship("Recipe", back_populates="ingredients")

    def __repr__(self):
        return f"<RecipeIngredient(recipe_id={self.recipe_id}, name='{self.name}', quantity={self.quantity})>"


class UserFavorite(Base, TimestampMixin):
    """User's favorite recipes."""

    __tablename__ = "user_favorites"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=False)
    rating = Column(Integer)  # 1-5 star rating
    notes = Column(Text)  # Personal notes about the recipe

    # Relationships
    user = relationship("User", back_populates="favorite_recipes")
    recipe = relationship("Recipe", back_populates="user_favorites")

    # Ensure unique user-recipe combinations
    __table_args__ = (UniqueConstraint('user_id', 'recipe_id', name='unique_user_recipe_favorite'),)

    def __repr__(self):
        return f"<UserFavorite(user_id={self.user_id}, recipe_id={self.recipe_id}, rating={self.rating})>"
