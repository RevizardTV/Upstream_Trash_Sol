from __future__ import annotations
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.recycling_model import RecyclingEntry

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(50), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    premise_type: Mapped[str] = mapped_column(String(50), default="house", server_default="house", nullable=False)
    household_size: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    upi_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    profile_complete: Mapped[bool] = mapped_column(default=True, server_default="1", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now(), nullable=False
    )

    recycling_entries: Mapped[List[RecyclingEntry]] = relationship(
        "RecyclingEntry", back_populates="user", cascade="all, delete-orphan"
    )