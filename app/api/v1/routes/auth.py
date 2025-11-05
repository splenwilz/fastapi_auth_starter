from typing import Union
from fastapi import APIRouter, HTTPException, Request, status
from workos.exceptions import BadRequestException, EmailVerificationRequiredException, NotFoundException

from app.api.v1.schemas.auth import EmailVerificationRequiredResponse, LoginRequest, LoginResponse, VerifyEmailRequest, VerifyEmailResponse, WorkOSLoginRequest, WorkOsVerifyEmailRequest
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


"""This endpoint is used to login a user with email and password.

Args:
    login_request: LoginRequest
    request: Request

Returns:
    Union[LoginResponse, EmailVerificationRequiredResponse]
"""
@router.post(
    "/login",
    response_model=Union[LoginResponse, EmailVerificationRequiredResponse],
    summary="Login a user with email and password",
    status_code=status.HTTP_200_OK
)
async def login(login_request: LoginRequest, request: Request) -> Union[LoginResponse, EmailVerificationRequiredResponse]:
    """
    This endpoint is used to login a user with email and password.

    Note: If the user is not verified, the endpoint will return an EmailVerificationRequiredResponse.

    Args:
        login_request: LoginRequest
        request: Request

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
            )
        
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
        )
    
    except NotFoundException as e:
        # User not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email address. Please sign up first."
        )
    
    except Exception as e:
        # Log but don't expose internal errors
        logger.error(f"Unexpected error during login: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )