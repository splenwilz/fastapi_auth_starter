from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from workos import WorkOSClient
from datetime import datetime, timezone
from app.core.config import settings
from app.core.exceptions import InvalidPasswordException
from app.models.user import User
from app.api.v1.schemas.user import UserCreate, UserUpdate

class UserService:
    def __init__(self):
        self.workos_client = WorkOSClient(
            api_key=settings.WORKOS_API_KEY,
            client_id=settings.WORKOS_CLIENT_ID
        )

    async def get_user(self, db: AsyncSession, user_id: str) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_users(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        result = await db.execute(select(User).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create_user(self, db: AsyncSession, user_data: UserCreate) -> User:
        result = await db.execute(select(User).where(User.email == user_data.email))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            return existing_user

        create_user_payload = {
            "email": user_data.email,
            "password": user_data.password,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
        }

        # Create user in WorkOS
        workos_user_response = self.workos_client.user_management.create_user(**create_user_payload)
        
        # Send verification email
        # On signup, we don't send the verification email to the user, because it will be sent later in the login process for the first time.
        # self.workos_client.user_management.send_verification_email(
        #     user_id=workos_user_response.id
        # )
        
        # Create user in database
        user = User(
            id=workos_user_response.id,
            email=workos_user_response.email,
            first_name=workos_user_response.first_name,
            last_name=workos_user_response.last_name
        )
        db.add(user)
        await db.flush()
        return user

    async def update_user(self, db: AsyncSession, user_id: str, user_data: UserUpdate):
        existing_user = await self.get_user(db, user_id)
        if not existing_user:
            return None

        
        update_user_payload = {
            "first_name": user_data.first_name,
            "last_name": user_data.last_name
        }

        self.workos_client.user_management.update_user(
            user_id=user_id,
            **update_user_payload
        )   
        
        update_data = user_data.model_dump(exclude_unset=True) # includes only fields that are set
        for field, value in update_data.items(): # update the existing user with the new data
            setattr(existing_user, field, value) # set the value of the field to the new value

        # Don't commit here - let the get_db() dependency handle commit/rollback
        await db.flush() # flush changes to database (without committing)
        # Don't refresh here - timestamps will be available after commit
        # In serverless, refreshing before commit can cause connection issues
        
        # Manually set updated_at since we can't reliably refresh in serverless environments
        existing_user.updated_at = datetime.now(timezone.utc)

        return existing_user

    
    async def delete_user(self, db: AsyncSession, user_id: str) -> bool:
        existing_user = await self.get_user(db, user_id)
        if not existing_user:
            return False
        
        self.workos_client.user_management.delete_user(
            user_id=user_id
        )

        await db.delete(existing_user)
        return True