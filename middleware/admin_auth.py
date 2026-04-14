"""Admin authentication — simple JWT-based PIN auth for mobile app."""

import jwt
import logging
from datetime import datetime, timedelta, timezone
from fastapi import Request, HTTPException
from config import settings

logger = logging.getLogger(__name__)

SECRET_KEY = "salon-admin-secret-key-2026"
ALGORITHM = "HS256"
TOKEN_EXPIRY_DAYS = 30


def create_admin_token() -> str:
    """Create a JWT token for admin access."""
    payload = {
        "role": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRY_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_admin_token(token: str) -> bool:
    """Verify an admin JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("role") == "admin"
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False


async def require_admin(request: Request):
    """FastAPI dependency — require valid admin token."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = auth_header.replace("Bearer ", "")
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
