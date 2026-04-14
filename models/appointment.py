"""Appointment model — booked salon appointments."""

from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Appointment(Base):
    """A booked appointment linking a customer, service, and stylist."""

    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False)
    stylist_id: Mapped[int] = mapped_column(Integer, ForeignKey("stylists.id"), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(15), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="booked")  # booked | cancelled | completed | rescheduled
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    service = relationship("Service")
    stylist = relationship("Stylist", back_populates="appointments")

    # Index for fast overlap detection
    __table_args__ = (
        Index("idx_stylist_time", "stylist_id", "start_time"),
        Index("idx_customer_phone", "customer_phone"),
    )

    def __repr__(self) -> str:
        return f"<Appointment(id={self.id}, service_id={self.service_id}, status={self.status})>"
