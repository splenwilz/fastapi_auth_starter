"""
Application configuration settings
Handles environment variables and configuration management
All configuration values should be set in .env file
Reference: https://fastapi.tiangolo.com/advanced/settings/
"""
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
    # MUST be set in .env file - no default to force explicit configuration
    DATABASE_URL: str
    
    # Alembic Configuration
    # Used for database migrations
    # Reference: https://alembic.sqlalchemy.org/en/latest/tutorial.html
    ALEMBIC_CONFIG: str = "alembic.ini"
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"  # Load from .env file (required)
        case_sensitive = True  # Environment variable names are case-sensitive


# Global settings instance
# Import this in other modules to access configuration
settings = Settings()

