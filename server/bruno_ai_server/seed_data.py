"""
Seed data for Bruno AI database.
"""

from sqlalchemy.orm import Session
from .models.pantry import PantryCategory


def seed_pantry_categories(db: Session):
    """Seed initial pantry categories."""
    
    categories = [
        {
            "name": "Fruits",
            "description": "Fresh and dried fruits",
            "icon": "🍎",
            "color": "#FF6B6B"
        },
        {
            "name": "Vegetables", 
            "description": "Fresh and frozen vegetables",
            "icon": "🥕",
            "color": "#4ECDC4"
        },
        {
            "name": "Dairy",
            "description": "Milk, cheese, yogurt, and dairy products",
            "icon": "🥛",
            "color": "#FFE66D"
        },
        {
            "name": "Meat & Seafood",
            "description": "Fresh and frozen meat, poultry, and seafood",
            "icon": "🥩",
            "color": "#FF8B94"
        },
        {
            "name": "Grains & Cereals",
            "description": "Rice, pasta, bread, and cereal products",
            "icon": "🌾",
            "color": "#95E1D3"
        },
        {
            "name": "Canned Goods",
            "description": "Canned vegetables, fruits, and prepared foods",
            "icon": "🥫",
            "color": "#A8E6CF"
        },
        {
            "name": "Condiments & Spices",
            "description": "Sauces, spices, herbs, and seasonings",
            "icon": "🧂",
            "color": "#FFEAA7"
        },
        {
            "name": "Snacks",
            "description": "Chips, crackers, nuts, and snack foods",
            "icon": "🍿",
            "color": "#DDA0DD"
        },
        {
            "name": "Beverages",
            "description": "Juices, sodas, coffee, tea, and other drinks",
            "icon": "🥤",
            "color": "#74B9FF"
        },
        {
            "name": "Frozen Foods",
            "description": "Frozen meals, vegetables, and desserts",
            "icon": "🧊",
            "color": "#00B894"
        },
        {
            "name": "Bakery",
            "description": "Bread, pastries, and baked goods",
            "icon": "🍞",
            "color": "#E17055"
        },
        {
            "name": "Other",
            "description": "Miscellaneous food items",
            "icon": "📦",
            "color": "#B2BEC3"
        }
    ]

    # Check if categories already exist
    existing_count = db.query(PantryCategory).count()
    if existing_count > 0:
        print(f"Pantry categories already exist ({existing_count} found). Skipping seed.")
        return

    # Add categories to database
    for category_data in categories:
        category = PantryCategory(**category_data)
        db.add(category)
    
    db.commit()
    print(f"Successfully seeded {len(categories)} pantry categories.")


def seed_all(db: Session):
    """Seed all initial data."""
    print("Starting database seeding...")
    seed_pantry_categories(db)
    print("Database seeding completed.")
