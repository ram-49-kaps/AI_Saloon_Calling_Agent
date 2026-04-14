"""Push notification service — sends Expo push notifications to admin devices."""

import logging
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.admin_device import AdminDevice

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


async def send_admin_push_notification(
    db: AsyncSession,
    title: str,
    body: str,
    data: dict = None,
):
    """Send push notification to all registered admin devices."""
    result = await db.execute(select(AdminDevice))
    devices = result.scalars().all()

    if not devices:
        logger.info("No admin devices registered for push notifications")
        return

    messages = []
    for device in devices:
        message = {
            "to": device.expo_push_token,
            "sound": "default",
            "title": title,
            "body": body,
            "priority": "high",
        }
        if data:
            message["data"] = data
        messages.append(message)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                EXPO_PUSH_URL,
                json=messages,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
            logger.info(f"Push notification sent: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send push notification: {e}")
