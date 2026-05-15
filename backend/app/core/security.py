"""
JWT authentication and password hashing utilities.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# ── Password Hashing ────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT Tokens ───────────────────────────────────────────────
def create_access_token(
    subject: str,
    extra_claims: Optional[dict] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(subject),
        "iat": now,
        "exp": now + expires_delta,
        "type": "access",
    }
    if extra_claims:
        claims.update(extra_claims)

    return jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """Create a signed JWT refresh token with a longer expiry."""
    expires_delta = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(subject),
        "iat": now,
        "exp": now + expires_delta,
        "type": "refresh",
    }
    return jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token. Returns claims or None."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def decode_refresh_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT refresh token. Returns claims or None."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None
