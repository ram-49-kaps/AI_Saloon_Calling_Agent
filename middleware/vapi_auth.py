"""Vapi authentication middleware — validates server secret."""

import logging

from fastapi import Request, HTTPException

from config import settings

logger = logging.getLogger(__name__)


async def verify_vapi_secret(request: Request):
    """
    Validate the x-vapi-secret header from Vapi.

    Vapi sends a secret header with every request to your server URL.
    This ensures only Vapi can call your webhook.
    """
    # Skip validation if no secret is configured (dev mode)
    if not settings.VAPI_SERVER_SECRET:
        return

    secret = request.headers.get("x-vapi-secret", "")

    if secret != settings.VAPI_SERVER_SECRET:
        logger.warning("Unauthorized Vapi webhook request - invalid secret")
        raise HTTPException(status_code=401, detail="Unauthorized")
