from fastapi import APIRouter, Depends, HTTPException, status
from workos.exceptions import BadRequestException
from app.api.v1.schemas.user import UserCreate, UserResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.user import UserService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.get("/")
async def get_users():
    return {"users": []}

@router.post(
    "", 
    response_model=UserResponse, 
    summary="Create user", 
    description="Create a new user", 
    status_code=status.HTTP_201_CREATED
)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Create a new user
    
    Args:
        db: Database session
        user_data: User creation data
        
    Returns:
        Created UserResponse object
    """
    user_service = UserService()
    try:
        user = await user_service.create_user(db, user_data)
        return user
    except BadRequestException as e:
        # Handle WorkOS validation errors
        if hasattr(e, 'errors') and e.errors:
            for error in e.errors:
                error_code = error.get('code', '')
                error_message = error.get('message', '')
                
                if error_code == 'email_not_available':
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Email address is already registered. Please use a different email or try logging in."
                    )
                
                # Handle other WorkOS errors if needed
                if error_code == 'invalid_email':
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid email address format"
                    )
        
        # Generic WorkOS error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {e.message if hasattr(e, 'message') else str(e)}"
        )
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the user"
        )