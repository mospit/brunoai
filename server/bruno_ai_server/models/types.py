"""
Database type compatibility helpers.
"""

import json
from sqlalchemy import JSON, TypeDecorator, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Dialect


class JSONType(TypeDecorator):
    """
    A JSON type that uses JSONB for PostgreSQL and JSON for SQLite/others.
    
    This provides compatibility between PostgreSQL JSONB and SQLite JSON,
    ensuring tests can run with in-memory SQLite while production uses PostgreSQL.
    """
    
    impl = Text
    cache_ok = True
    
    def load_dialect_impl(self, dialect: Dialect):
        """Load the appropriate JSON type for the dialect."""
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())
    
    def process_bind_param(self, value, dialect):
        """Process parameters when binding to database."""
        if value is None:
            return value
        
        if dialect.name == 'postgresql':
            # PostgreSQL JSONB handles dict/list directly
            return value
        else:
            # For SQLite and others, serialize to JSON string
            return json.dumps(value) if value is not None else None
    
    def process_result_value(self, value, dialect):
        """Process values when retrieving from database."""
        if value is None:
            return value
        
        if dialect.name == 'postgresql':
            # PostgreSQL JSONB returns dict/list directly
            return value
        else:
            # For SQLite and others, deserialize from JSON string
            try:
                return json.loads(value) if isinstance(value, str) else value
            except (json.JSONDecodeError, TypeError):
                return value


# Export a common JSONB type that works across dialects
CompatibleJSONB = JSONType
