"""
Alembic environment configuration
Handles database migrations with SQLAlchemy
Reference: https://alembic.sqlalchemy.org/en/latest/tutorial.html
"""
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, text

from alembic import context

# Import Base for models
from app.core.database import Base

# Lazy import settings - only load when DATABASE_URL is needed
# This prevents errors when .env file doesn't exist yet
def get_settings():
    """
    Lazy load settings to avoid validation errors before .env is configured.
    
    Catches validation errors and provides helpful instructions.
    """
    try:
        from app.core.config import settings
        return settings
    except Exception as e:
        import sys
        print(
            "\n❌ Error: Environment variables not configured. Please set up your .env file first:\n"
            "   1. Copy .env.example to .env: cp .env.example .env\n"
            "   2. Edit .env and configure required variables:\n"
            "      - DATABASE_URL (PostgreSQL connection string)\n"
            "      - WORKOS_API_KEY\n"
            "      - WORKOS_CLIENT_ID\n"
            "      - WORKOS_ALLOWED_REDIRECT_URIS\n"
            "   3. Then run this command again\n",
            file=sys.stderr
        )
        raise

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
    try:
        settings = get_settings()
        # Convert asyncpg URL to psycopg2 URL (sync driver for migrations)
        db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        # Escape % for ConfigParser (double % to prevent interpolation)
        db_url = db_url.replace("%", "%%")
        config.set_main_option("sqlalchemy.url", db_url)
    except Exception as e:
        # Settings not configured yet - error message already shown by get_settings()
        raise

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
        # Auto-fix: If alembic_version table exists but references a deleted migration,
        # drop it so users can start fresh without manual intervention
        # Reference: https://alembic.sqlalchemy.org/en/latest/branches.html#working-with-multiple-bases
        try:
            result = connection.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
            row = result.fetchone()
            if row:
                current_rev = row[0]
                # Check if the revision exists in the versions directory
                from alembic.script import ScriptDirectory  # type: ignore[import-untyped]
                script = ScriptDirectory.from_config(config)
                try:
                    script.get_revision(current_rev)
                except Exception:
                    # Revision doesn't exist - drop the table to start fresh
                    connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
                    connection.commit()
        except Exception:
            # Table doesn't exist or other error - that's fine, continue
            pass

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
