from typing import Optional
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


class WorkOSImpersonatorResponse(BaseModel):
    email: str | None = Field(None, description="Impersonator email")
    reason: str | None = Field(None, description="Impersonation reason")


class VerifyEmailResponse(BaseModel):
    access_token: str | None = Field(None, description="Access token")
    refresh_token: str | None = Field(None, description="Refresh token")
    authentication_method: str | None = Field(None, description="Authentication method")
    impersonator: WorkOSImpersonatorResponse | None = Field(None, description="Impersonator")
    organization_id: str | None = Field(None, description="Organization ID")
    user: WorkOSUserResponse | None = Field(None, description="User")
    sealed_session: str | None = Field(None, description="Sealed session")


# In app/api/v1/schemas/auth.py
from pydantic import BaseModel, Field, model_validator

class AuthorizationRequest(BaseModel):
    """
    Request to generate OAuth2 authorization URL.
    
    Supports two patterns:
    1. AuthKit: Use provider="authkit" (unified interface)
    2. SSO: Use connection_id (direct provider connection)
    
    Exactly one of provider or connection_id must be provided.
    """
    provider: str | None = Field(
        None,
        description="AuthKit provider (use 'authkit' for unified interface). Mutually exclusive with connection_id."
    )
    connection_id: str | None = Field(
        None,
        description="WorkOS SSO connection ID for direct provider (e.g., Google, Microsoft). Mutually exclusive with provider."
    )
    redirect_uri: str = Field(
        ...,
        description="URI to redirect to after authentication. Must be in allowed list."
    )
    state: str | None = Field(
        None,
        description="Optional state parameter for CSRF protection"
    )
    
    @model_validator(mode='after')
    def validate_provider_or_connection(self):
        """Ensure exactly one of provider or connection_id is provided"""
        has_provider = self.provider is not None
        has_connection = self.connection_id is not None
        
        if not has_provider and not has_connection:
            raise ValueError("Either 'provider' or 'connection_id' must be provided")
        
        if has_provider and has_connection:
            raise ValueError("'provider' and 'connection_id' are mutually exclusive. Provide only one.")
        
        return self

class WorkOSAuthorizationRequest(AuthorizationRequest):
    pass

class OAuthCallbackRequest(BaseModel):
    code: str = Field(..., description="Authorization code from OAuth callback")
    state: str | None = Field(None, description="State parameter for CSRF verification")