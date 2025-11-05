from time import timezone
from sqlalchemy.ext.asyncio import AsyncSession
from workos import WorkOSClient
from datetime import datetime, timedelta
from app.core.config import settings
from app.models.user import User
from app.api.v1.schemas.user import UserCreate

class UserService:
    def __init__(self):
        self.workos_client = WorkOSClient(
            api_key=settings.WORKOS_API_KEY,
            client_id=settings.WORKOS_CLIENT_ID
        )

    async def create_user(self, db: AsyncSession, user_data: UserCreate) -> User:
        
        create_user_payload = {
            "email": user_data.email,
            "password": user_data.password,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
        }

        # Create user in WorkOS
        workos_user_response = self.workos_client.user_management.create_user(**create_user_payload)
        
        # Send verification email
        self.workos_client.user_management.send_verification_email(
            user_id=workos_user_response.id
        )
        
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