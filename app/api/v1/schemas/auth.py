from pydantic import BaseModel, Field
from app.api.v1.schemas.user import UserResponse
from datetime import datetime

class EmailVerificationRequiredResponse(BaseModel):
    message: str
    pending_authentication_token: str
    email_verification_id: str
    email: str
    requires_verification: bool = True

class VerifyEmailRequest(BaseModel):
    pending_authentication_token: str = Field(..., description="Pending authentication token")
    code: str = Field(..., description="Code")

class WorkOsVerifyEmailRequest(VerifyEmailRequest):
    ip_address: str = Field(..., description="User IP address")
    user_agent: str = Field(..., description="User user agent")



class LoginRequest(BaseModel):
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")

class WorkOSLoginRequest(LoginRequest):
    ip_address: str = Field(..., description="User IP address")
    user_agent: str = Field(..., description="User user agent")

class WorkOSUserResponse(BaseModel):
    object: str = Field(..., description="Object")
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    first_name: str | None = Field(None, description="User first name")
    last_name: str | None = Field(None, description="User last name") 
    email_verified: bool = Field(..., description="User email verified")
    profile_picture_url: str | None = Field(None, description="User profile picture URL")
    created_at: datetime = Field(..., description="User created at")
    updated_at: datetime = Field(..., description="User updated at")

    class Config:
        from_attributes = True
    

class LoginResponse(BaseModel):
    user: WorkOSUserResponse = Field(..., description="User")
    organization_id: str | None = Field(None, description="Organization ID")
    access_token: str = Field(..., description="Access token")
    refresh_token: str = Field(..., description="Refresh token")



class VerifyEmailResponse(BaseModel):
    access_token: str = Field(..., description="Access token")
    refresh_token: str = Field(..., description="Refresh token")
    authentication_method: str = Field(..., description="Authentication method")
    impersonator: str = Field(..., description="Impersonator")
    organization_id: str = Field(..., description="Organization ID")
    user: WorkOSUserResponse = Field(..., description="User")
    sealed_session: str = Field(..., description="Sealed session")