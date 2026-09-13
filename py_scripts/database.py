from datetime import datetime
from decimal import Decimal
from typing import Generator, List, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    create_engine,
    func,
    text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

from py_scripts.config import config

# 1. Database Connection Engine
engine = create_engine(
    config.DB_URL,
    connect_args={"ssl": {"ca": "/etc/ssl/certs/ca-certificates.crt"}},
    pool_pre_ping=True,
)

# 2. Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 3. Base Declarative Class
class Base(DeclarativeBase):
    pass


# 4. Database Models
class StaffProfile(Base):
    __tablename__ = "staff_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    assigned_pincode: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    
    # Dual default prevents MySQL 1364 if DB column lacks DEFAULT expression
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now(), nullable=False
    )

    # Relationships
    reviewed_entries: Mapped[List["RecyclingEntry"]] = relationship(
        "RecyclingEntry", back_populates="reviewed_by_staff"
    )


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
    
    # Explicit defaults for MySQL compatibility
    profile_complete: Mapped[bool] = mapped_column(default=True, server_default="1", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now(), nullable=False
    )

    # Bidirectional Relationship (Option 2 aligned)
    recycling_entries: Mapped[List["RecyclingEntry"]] = relationship(
        "RecyclingEntry", back_populates="user", cascade="all, delete-orphan"
    )


class RecyclingEntry(Base):
    __tablename__ = "recycling_entries"

    entry_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    waste_category: Mapped[str] = mapped_column(String(100), nullable=False)
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payout_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    status: Mapped[str] = mapped_column(
        Enum("pending", "approved", "declined", name="status_enum"),
        default="pending",
        server_default="pending",
        nullable=False,
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reviewed_by_staff_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("staff_profiles.id", ondelete="SET NULL"), nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["UserProfile"] = relationship("UserProfile", back_populates="recycling_entries")
    reviewed_by_staff: Mapped[Optional["StaffProfile"]] = relationship(
        "StaffProfile", back_populates="reviewed_entries"
    )


# 5. Database Dependency
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 6. Connection Test & Initialization
def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connection successful! Result:", result.scalar())
    except Exception as e:
        print("❌ Database connection failed!")
        print("Error details:", e)


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    test_connection()