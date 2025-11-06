import asyncio
from workos import WorkOSClient
from app.api.v1.schemas.auth import LoginResponse, WorkOSAuthorizationRequest, WorkOSLoginRequest, WorkOsVerifyEmailRequest
from app.core.config import settings

class AuthService:
    def __init__(self):
        self.workos_client = WorkOSClient(
            api_key=settings.WORKOS_API_KEY,
            client_id=settings.WORKOS_CLIENT_ID
        )

    async def verify_email(self, verify_email_request: WorkOsVerifyEmailRequest):
        # Offload synchronous WorkOS call to thread pool to avoid blocking event loop
        # Reference: https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread
        response = await asyncio.to_thread(
            self.workos_client.user_management.authenticate_with_email_verification,
            code=verify_email_request.code,
            pending_authentication_token=verify_email_request.pending_authentication_token,
            ip_address=verify_email_request.ip_address,
            user_agent=verify_email_request.user_agent
        )
        return response

    async def login(self, login_request: WorkOSLoginRequest) -> LoginResponse:
        # Offload synchronous WorkOS call to thread pool to avoid blocking event loop
        response = await asyncio.to_thread(
            self.workos_client.user_management.authenticate_with_password,
            email=login_request.email,
            password=login_request.password,
            ip_address=login_request.ip_address,
            user_agent=login_request.user_agent
        )
        return LoginResponse(
            user=response.user,
            organization_id=response.organization_id,
            access_token=response.access_token,
            refresh_token=response.refresh_token
        )

    # # Generate OAuth2 authorization URL
    # In app/services/auth.py
    async def generate_oauth2_authorization_url(
        self, 
        authorization_request: WorkOSAuthorizationRequest
    ) -> str:
        """
        Generate OAuth2 authorization URL.
        
        Supports two patterns:
        1. AuthKit: provider="authkit" → Unified authentication interface
        2. SSO: connection_id="conn_xxx" → Direct provider connection
        
        Args:
            authorization_request: Request containing either provider or connection_id
            
        Returns:
            Authorization URL string
        """
        params = {
            "redirect_uri": authorization_request.redirect_uri,
        }
        
        # Add state if provided
        if authorization_request.state:
            params["state"] = authorization_request.state
        
        # Determine which pattern to use
        if authorization_request.provider:
            # AuthKit pattern
            params["provider"] = authorization_request.provider
        elif authorization_request.connection_id:
            # SSO pattern
            params["connection_id"] = authorization_request.connection_id
        
        # Offload synchronous WorkOS call to thread pool to avoid blocking event loop
        authorization_url = await asyncio.to_thread(
            self.workos_client.user_management.get_authorization_url,
            **params
        )
        return authorization_url


    async def oauth2_callback(
        self, 
        code: str
    ) -> LoginResponse:
        """
        Exchange a OAuth2 code for access token and refresh token.
        
        Args:
            code: OAuth2 code
            
        Returns:
            LoginResponse: Access token and refresh token
        """
        # Offload synchronous WorkOS call to thread pool to avoid blocking event loop
        response = await asyncio.to_thread(
            self.workos_client.user_management.authenticate_with_code,
            code=code
        )
        return LoginResponse(
            user=response.user,
            organization_id=response.organization_id,
            access_token=response.access_token,
            refresh_token=response.refresh_token
        )