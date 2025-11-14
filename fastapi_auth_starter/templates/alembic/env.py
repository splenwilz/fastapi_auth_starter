"""
Alembic environment configuration
Handles database migrations with SQLAlchemy
Reference: https://alembic.sqlalchemy.org/en/latest/tutorial.html
"""
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Import application settings and Base
from app.core.config import settings
from app.core.database import Base

# Import all models here so Alembic can detect them for autogenerate
# As models are added, import them here
from app.models import Task, User 
# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url from settings if not set in alembic.ini
# Convert asyncpg URL to psycopg2 URL for Alembic (Alembic uses sync drivers)
# Reference: https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls
if not config.get_main_option("sqlalchemy.url"):
    # Convert asyncpg URL to psycopg2 URL (sync driver for migrations)
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    # Escape % for ConfigParser (double % to prevent interpolation)
    db_url = db_url.replace("%", "%%")
    config.set_main_option("sqlalchemy.url", db_url)

# Set target_metadata for autogenerate support
# This tells Alembic what models exist in the application
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    
    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine
    and associate a connection with the context.
    
    Reference: https://alembic.sqlalchemy.org/en/latest/tutorial.html#run-a-migration
    """
    # Create sync engine from configuration
    # Alembic uses sync SQLAlchemy operations
    # We use psycopg2 (sync) for migrations, asyncpg (async) for the app
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Don't pool connections for migrations
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Compare column types when autogenerating
            compare_server_default=True,  # Compare server defaults
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
