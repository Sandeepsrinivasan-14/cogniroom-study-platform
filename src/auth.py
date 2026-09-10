import os
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

# SECRET_KEY must come from the environment. In DEBUG mode we fall back to a
# random ephemeral key (tokens won't survive a restart) so local dev still runs;
# in production a missing SECRET_KEY is a hard error.
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    if os.environ.get("DEBUG", "").lower() in ("1", "true", "yes"):
        SECRET_KEY = secrets.token_urlsafe(48)
        print("[WARN] SECRET_KEY not set - using a random ephemeral key (DEBUG only)")
    else:
        raise RuntimeError("SECRET_KEY environment variable is required")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = HTTPBearer()


def get_password_hash(password: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _looks_like_bcrypt(hashed: str) -> bool:
    return hashed.startswith(("$2a$", "$2b$", "$2y$"))


def _legacy_sha256(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password.

    Supports both bcrypt hashes (current) and the legacy unsalted SHA-256
    hashes (older accounts) so existing users can still log in. Callers that
    want to upgrade a legacy hash should re-hash with get_password_hash on a
    successful login.
    """
    if not hashed_password:
        return False
    if _looks_like_bcrypt(hashed_password):
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except ValueError:
            return False
    # Legacy fallback: constant-time compare of SHA-256 hex digests.
    return hmac.compare_digest(_legacy_sha256(plain_password), hashed_password)


def needs_rehash(hashed_password: str) -> bool:
    """True if the stored hash is a legacy format that should be upgraded."""
    return not _looks_like_bcrypt(hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user
