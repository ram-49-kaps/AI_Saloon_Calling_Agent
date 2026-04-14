"""Service model — salon services with multilingual aliases."""

from sqlalchemy import String, Integer, Float, Boolean, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Service(Base):
    """A salon service (e.g., Haircut, Facial, etc.)."""

    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)  # minutes
    price: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<Service(name={self.name}, duration={self.duration}min, price=₹{self.price})>"
