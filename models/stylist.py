"""Stylist model — salon staff with working hours and specializations."""

from sqlalchemy import String, Integer, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Stylist(Base):
    """A salon stylist/artist."""

    __tablename__ = "stylists"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(15), nullable=False)
    specializations: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    work_start: Mapped[str] = mapped_column(String(5), nullable=False, default="09:00")
    work_end: Mapped[str] = mapped_column(String(5), nullable=False, default="20:00")
    days_off: Mapped[list[int]] = mapped_column(ARRAY(Integer), default=[0])  # 0=Sunday
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationship
    appointments = relationship("Appointment", back_populates="stylist")

    def __repr__(self) -> str:
        return f"<Stylist(name={self.name}, specs={self.specializations})>"
