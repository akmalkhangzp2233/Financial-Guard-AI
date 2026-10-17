"""
FinGuard AI Authentication Helpers

Features:
- Secure password hashing and verification
- JWT access-token generation and validation
- OAuth2 Bearer-token authentication
- Current-user and administrator dependencies

IMPORTANT:
Set JWT_SECRET in your environment before production deployment.
Never commit real secrets to GitHub.
"""

import os
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from passlib.context import CryptContext

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session

from database import get_db
import models


# --------------------------------------------------
# Configuration
# --------------------------------------------------

SECRET_KEY = os.getenv(
    "JWT_SECRET",
    "change-this-in-your-.env-file",
)

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


# --------------------------------------------------
# Password Hashing
# --------------------------------------------------

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """Hash a password before storing it in the database."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its stored hash."""
    return pwd_context.verify(plain, hashed)


# --------------------------------------------------
# OAuth2 Configuration
# --------------------------------------------------
#
# Swagger uses /auth/token to obtain an access token.
# The frontend can continue using /auth/login with JSON.
# --------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
)


# --------------------------------------------------
# JWT Token Generation
# --------------------------------------------------

def create_access_token(data: dict) -> str:
    """
    Generate a signed JWT access token.

    The token includes an expiration timestamp.
    """
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode["exp"] = expire

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


# --------------------------------------------------
# Current User Authentication
# --------------------------------------------------

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """
    Decode the JWT and retrieve the authenticated user.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        # Validate the subject before querying the database.
        user_id = int(user_id)

    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled",
        )

    return user


# --------------------------------------------------
# Administrator Authentication
# --------------------------------------------------

def get_current_admin(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    Allow access only to active administrator accounts.
    """

    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user