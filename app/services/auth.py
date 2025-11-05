from workos import WorkOSClient
from app.api.v1.schemas.auth import LoginResponse, WorkOSLoginRequest, WorkOsVerifyEmailRequest
from app.core.config import settings

class AuthService:
    def __init__(self):
        self.workos_client = WorkOSClient(
            api_key=settings.WORKOS_API_KEY,
            client_id=settings.WORKOS_CLIENT_ID
        )

    async def verify_email(self, verify_email_request: WorkOsVerifyEmailRequest):
        response = self.workos_client.user_management.authenticate_with_email_verification(
            code=verify_email_request.code,
            pending_authentication_token=verify_email_request.pending_authentication_token,
            ip_address=verify_email_request.ip_address,
            user_agent=verify_email_request.user_agent
        )
        return response

    async def login(self, login_request: WorkOSLoginRequest) -> LoginResponse:
        response = self.workos_client.user_management.authenticate_with_password(
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