from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Linked OTP Verification Email
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    premise_type: Mapped[str] = mapped_column(String(50), default="house")
    household_size: Mapped[int] = mapped_column(default=1)
    
    upi_id: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    profile_complete: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )