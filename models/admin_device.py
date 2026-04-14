"""Admin device model — stores Expo push tokens for notifications."""

from sqlalchemy import Column, Integer, String, DateTime, func

from database import Base


class AdminDevice(Base):
    """Stores Expo Push Tokens for admin devices."""
    __tablename__ = "admin_devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    expo_push_token = Column(String, unique=True, nullable=False, index=True)
    device_name = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
