"""CallLog model — stores call transcripts, outcomes, and feedback ratings."""

from datetime import datetime

from sqlalchemy import String, Integer, Float, DateTime, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class CallLog(Base):
    """Stores data from every Vapi call for analytics and improvement."""

    __tablename__ = "call_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Call metadata from Vapi
    vapi_call_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0)
    ended_reason: Mapped[str] = mapped_column(String(50), nullable=True)  # e.g. "customer-ended", "assistant-ended"

    # Transcript & summary
    transcript: Mapped[str] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)

    # Outcome tracking
    booking_succeeded: Mapped[bool] = mapped_column(Boolean, default=False)
    tool_calls_count: Mapped[int] = mapped_column(Integer, default=0)
    tool_errors_count: Mapped[int] = mapped_column(Integer, default=0)

    # Customer feedback (1-5 stars, collected via SMS)
    feedback_rating: Mapped[int] = mapped_column(Integer, nullable=True)
    feedback_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    call_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<CallLog(id={self.id}, call={self.vapi_call_id}, rating={self.feedback_rating})>"
