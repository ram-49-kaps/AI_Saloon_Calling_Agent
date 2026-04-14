"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App settings loaded from environment variables."""

    PORT: int = 80
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/salon_booking"
    VAPI_SERVER_SECRET: str = ""

    # SMS notifications (Twilio)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    SALON_OWNER_PHONE: str = ""  # Owner gets notified on every booking
    ADMIN_PIN: str = "1234"  # Mobile app admin login PIN

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Convert any postgres:// URL to postgresql+asyncpg:// for SQLAlchemy."""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    # Sync URL for Alembic / seed scripts
    @property
    def SYNC_DATABASE_URL(self) -> str:
        return self.DATABASE_URL.replace("+asyncpg", "")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
