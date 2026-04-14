"""Customer model — salon customers."""

from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Customer(Base):
    """A salon customer identified by phone number."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(15), unique=True, index=True, nullable=False)
    preferred_language: Mapped[str] = mapped_column(String(5), default="en")
    total_visits: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return f"<Customer(name={self.name}, phone={self.phone})>"
