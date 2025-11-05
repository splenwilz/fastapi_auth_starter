"""
Application configuration settings
Handles environment variables and configuration management
All configuration values should be set in .env file or environment variables
Reference: https://fastapi.tiangolo.com/advanced/settings/
"""
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    Uses pydantic BaseSettings for validation and type conversion
    
    All values should be set in .env file (see .env.example for template)
    """
    # API Configuration
    # These can have defaults but should be overridden in .env
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "FastAPI Auth Starter"
    VERSION: str = "0.1.0"
    
    # Database Configuration
    # PostgreSQL connection string format: postgresql+asyncpg://user:password@host:port/dbname
    # Reference: https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls
    # Set in .env file or Vercel environment variables
    # Note: Special characters in password must be URL-encoded (e.g., ! = %21)
    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL database URL. Must be set via environment variable."
    )

    # WorkOS Configuration
    # WorkOS API key for user management
    # Reference: https://workos.com/docs/reference/api-reference/user-management
    WORKOS_API_KEY: str = Field(
        ...,
        description="WorkOS API key. Must be set via environment variable."
    )
    WORKOS_CLIENT_ID: str = Field(
        ...,
        description="WorkOS client ID. Must be set via environment variable."
    )
    # Alembic Configuration
    # Used for database migrations
    # Reference: https://alembic.sqlalchemy.org/en/latest/tutorial.html
    ALEMBIC_CONFIG: str = "alembic.ini"
    
    # Pydantic v2 configuration
    # Reference: https://docs.pydantic.dev/latest/api/config/
    model_config = ConfigDict(
        env_file=".env",  # Load from .env file (required)
        case_sensitive=True,  # Environment variable names are case-sensitive
        extra="ignore",  # Ignore extra environment variables not defined in this class
        # This allows additional env vars (like WorkOS config) to exist without causing validation errors
    )


# Global settings instance
# Import this in other modules to access configuration
settings = Settings()

