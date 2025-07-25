"""
Alembic migrate environment configuration
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, text

from alembic import context
from bruno_ai_server.config import settings

# Ensures all models are imported
from bruno_ai_server.models import *  # noqa: F401, F403
from bruno_ai_server.models.base import Base

# this is the Alembic Config object, which provides
# the access to the values within the .ini file in use.
config = context.config


# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# Add models to metadata
target_metadata = Base.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.




def get_url():
    """Get database URL from settings or config."""
    try:
        return settings.db_url
    except Exception:
        # Fallback to alembic config URL if settings fail
        return config.get_main_option("sqlalchemy.url")


def run_migrations_offline():
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string
    to the script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        # Ensure uuid-ossp extension is available for offline mode
        context.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        context.run_migrations()


def run_migrations_online():
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Ensure uuid-ossp extension is available
        connection.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
