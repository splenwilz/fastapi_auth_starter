from typing import Union
from fastapi import APIRouter, HTTPException, Request, status
from workos.exceptions import BadRequestException, EmailVerificationRequiredException, NotFoundException

from app.api.v1.schemas.auth import AuthorizationRequest, EmailVerificationRequiredResponse, LoginRequest, LoginResponse, OAuthCallbackRequest, VerifyEmailRequest, VerifyEmailResponse, WorkOSAuthorizationRequest, WorkOSLoginRequest, WorkOsVerifyEmailRequest
from app.core.config import settings
from app.services.auth import AuthService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/verify-email",
    response_model=VerifyEmailResponse,
    summary="Verify an email address",
    status_code=status.HTTP_200_OK
    )
async def verify_email(verify_email_request: VerifyEmailRequest, request: Request):
    """This endpoint is used to verify an email address.

    Args:
        verify_email_request: WorkOsVerifyEmailRequest
        request: Request

    Returns:
        VerifyEmailResponse
    """
    auth_service = AuthService()
    try:
        workos_verify_email_request = WorkOsVerifyEmailRequest(
            pending_authentication_token=verify_email_request.pending_authentication_token,
            code=verify_email_request.code,
            ip_address=request.client.host if request.client else "",
            user_agent=request.headers.get("user-agent") or ""
        )
        return await auth_service.verify_email(verify_email_request=workos_verify_email_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post(
    "/login",
    response_model=Union[LoginResponse, EmailVerificationRequiredResponse],
    summary="Login a user with email and password",
    status_code=status.HTTP_200_OK
)
async def login(login_request: LoginRequest, request: Request) -> Union[LoginResponse, EmailVerificationRequiredResponse]:
    """
    Authenticate a user via email and password.

    If the user is not verified, returns an `EmailVerificationRequiredResponse`
    containing a `pending_authentication_token` and `email_verification_id`.
    These are used with the code sent to the user’s email to complete verification
    through the `verify-email` endpoint.

    Args:
        login_request (LoginRequest): User credentials.
        request (Request): Current HTTP request context.

    Returns:
        Union[LoginResponse, EmailVerificationRequiredResponse]
    """


    
    auth_service = AuthService()
    
    try:
        workos_login_request = WorkOSLoginRequest(
            email=login_request.email,
            password=login_request.password,
            ip_address=request.client.host if request.client else "",
            user_agent=request.headers.get("user-agent") or ""
        )
        
        return await auth_service.login(login_request=workos_login_request)
    
    except EmailVerificationRequiredException as e:
        response_data = e.response_json
        
        return EmailVerificationRequiredResponse(
            message="Email verification required",
            pending_authentication_token=response_data.get('pending_authentication_token'),
            email_verification_id=response_data.get('email_verification_id'),
            email=response_data.get('email', login_request.email),
            requires_verification=True
        )
    
    except BadRequestException as e:
        # Handle WorkOS validation errors
        error_code = getattr(e, 'code', None)
        
        # Invalid credentials
        if error_code == 'invalid_credentials':
            logger.warning(f"Invalid login attempt for email: {login_request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password. Please check your credentials and try again."
            ) from e
        
        # Check errors array if present
        if hasattr(e, 'errors') and e.errors:
            for error in e.errors:
                error_code = error.get('code', '')
                
                if error_code == 'invalid_email':
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid email address format"
                    )
        
        # Generic BadRequest
        logger.warning(f"BadRequest during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {e.message if hasattr(e, 'message') else str(e)}"
        ) from e
    
    except NotFoundException:
        # User not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email address. Please sign up first."
        ) from None
    
    except Exception as e:
        # Log but don't expose internal errors
        logger.error(f"Unexpected error during login: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        ) from e

@router.post(
    "/authorize",
    summary="Generate OAuth2 authorization URL",
    
    status_code=status.HTTP_200_OK
)
async def authorize(authorization_request: AuthorizationRequest) -> dict:
    """
    Generate an OAuth2 authorization URL.
     The supported provider values are `GoogleOAuth`, `MicrosoftOAuth`, `GitHubOAuth`, and `AppleOAuth`. 
    
    Frontend can choose:
    - `provider="authkit"`: For unified interface with multiple auth methods
    - `connection_id="conn_xxx"`: For direct provider connection (better UX for specific buttons)

    Args:
        authorization_request (AuthorizationRequest): Authorization request.

    Returns:
        dict: Authorization URL.
    """
    # Validate redirect_uri against whitelist (security requirement)
    if authorization_request.redirect_uri not in settings.allowed_redirect_uris_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid redirect_uri. Must be one of: {settings.allowed_redirect_uris_list}"
        )
    
    # For SSO: Use default connection_id if not provided
    if authorization_request.connection_id and not authorization_request.provider:
        # SSO pattern - connection_id provided
        workos_request = WorkOSAuthorizationRequest(
            connection_id=authorization_request.connection_id,
            redirect_uri=authorization_request.redirect_uri,
            state=authorization_request.state
        )
    elif authorization_request.provider:
        # AuthKit pattern
        workos_request = WorkOSAuthorizationRequest(
            provider=authorization_request.provider,
            redirect_uri=authorization_request.redirect_uri,
            state=authorization_request.state
        )
    else:
        # Fallback: Try default connection_id if available
        if settings.WORKOS_DEFAULT_CONNECTION_ID:
            workos_request = WorkOSAuthorizationRequest(
                connection_id=settings.WORKOS_DEFAULT_CONNECTION_ID,
                redirect_uri=authorization_request.redirect_uri,
                state=authorization_request.state
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'provider' or 'connection_id' must be provided"
            ) 
    
    auth_service = AuthService()
    try:
        authorization_url = await auth_service.generate_oauth2_authorization_url(workos_request)
        return {"authorization_url": authorization_url}
    except Exception as e:
        logger.error(f"Error generating authorization URL: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authorization URL"
        ) from e

@router.post(
    "/callback",
    response_model=LoginResponse,
    summary="Exchange OAuth2 code for access token and refresh token",
    status_code=status.HTTP_200_OK
)
async def callback(callback_request: OAuthCallbackRequest) -> LoginResponse:
    """
    Exchange an OAuth2 code for access and refresh token.

    Args:
        callback_request (OAuthCallbackRequest): Callback request.

    Returns:
        LoginResponse: Access token and refresh token
    """
    auth_service = AuthService()
    try:
        return await auth_service.oauth2_callback(code=callback_request.code)
    except BadRequestException as e:
        error_code = getattr(e, 'code', None)
        error_description = getattr(e, 'error_description', '')
        if 'invalid_grant' in error_description or error_code == 'invalid_grant':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired authorization code. Please request a new authorization code."
            ) from e
        if error_code == 'invalid_credentials':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            ) from e
        if error_code == 'invalid_code':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid code"
            ) from e
        logger.error(f"Error exchanging OAuth2 code: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange OAuth2 code"
        ) from e
    except Exception as e:
        logger.error(f"Error exchanging OAuth2 code: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to exchange OAuth2 code"
        ) from e