"""
FinGuard AI Authentication Routes

Endpoints:
- POST /auth/register : Register a new account
- POST /auth/login    : JSON login for the frontend
- POST /auth/token    : OAuth2 form login for Swagger
- GET  /auth/me       : Return the authenticated user
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)

from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session

import models
import schemas

from database import get_db

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

from rate_limit import limiter


# --------------------------------------------------
# Router Configuration
# --------------------------------------------------

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


# --------------------------------------------------
# Register
# --------------------------------------------------

@router.post(
    "/register",
    response_model=schemas.UserOut,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
def register(
    request: Request,
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new user.

    The first registered user is automatically assigned
    administrator privileges, matching the existing
    FinGuard AI demo behavior.
    """

    existing_user = (
        db.query(models.User)
        .filter(models.User.email == payload.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Preserve the existing first-user administrator behavior.
    is_first_user = db.query(models.User.id).first() is None

    user = models.User(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        is_admin=is_first_user,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# --------------------------------------------------
# Frontend Login — JSON
# --------------------------------------------------

@router.post(
    "/login",
    response_model=schemas.Token,
)
@limiter.limit("5/minute")
def login(
    request: Request,
    payload: schemas.UserLogin,
    db: Session = Depends(get_db),
):
    """
    JSON login endpoint used by the existing React frontend.

    Expected request:
    {
        "email": "user@example.com",
        "password": "your-password"
    }
    """

    user = (
        db.query(models.User)
        .filter(models.User.email == payload.email)
        .first()
    )

    if not user or not verify_password(
        payload.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled",
        )

    token = create_access_token(
        {"sub": str(user.id)}
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }


# --------------------------------------------------
# Swagger Login — OAuth2 Form
# --------------------------------------------------

@router.post(
    "/token",
    response_model=schemas.Token,
)
@limiter.limit("5/minute")
def swagger_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    OAuth2-compatible login endpoint for Swagger.

    Swagger submits form fields:
    - username
    - password

    The username field contains the user's email address.

    This endpoint is separate from /login so that the
    existing frontend's JSON login continues to work.
    """

    user = (
        db.query(models.User)
        .filter(models.User.email == form_data.username)
        .first()
    )

    if not user or not verify_password(
        form_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled",
        )

    token = create_access_token(
        {"sub": str(user.id)}
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }


# --------------------------------------------------
# Current User
# --------------------------------------------------

@router.get(
    "/me",
    response_model=schemas.UserOut,
)
def get_me(
    current_user: models.User = Depends(get_current_user),
):
    """
    Return the currently authenticated user's profile.
    """

    return current_user