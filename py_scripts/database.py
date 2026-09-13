from datetime import datetime, timezone
from decimal import Decimal
from typing import Generator, List, Optional
from sqlalchemy import create_engine, text,Enum, String, ForeignKey,Numeric,func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session, relationship
from py_scripts.config import config

# 1. Database Connection Engine
engine = create_engine(
    config.DB_URL,
    connect_args={"ssl": {"ca": "/etc/ssl/certs/ca-certificates.crt"}},
    pool_pre_ping=True
)

# 2. Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Base Declarative Class


# 4. Database Models




# Modern SQLAlchemy 2.0 Base class definition
class Base(DeclarativeBase):
    pass

class StaffProfile(Base):
    __tablename__ = "staff_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    assigned_pincode: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class RecyclingEntry(Base):
    __tablename__ = "recycling_entries"

    entry_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    waste_category: Mapped[str] = mapped_column(String(100), nullable=False)
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payout_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # New Audit Fields
    status: Mapped[str] = mapped_column(Enum("pending", "approved", "declined", name="status_enum"), default="pending", nullable=False)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reviewed_by_staff_id: Mapped[Optional[int]] = mapped_column(ForeignKey("staff_profiles.id", ondelete="SET NULL"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["UserProfile"] = relationship("UserProfile", back_populates="entries")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    premise_type: Mapped[str] = mapped_column(String(50), default="house", nullable=False)
    household_size: Mapped[int] = mapped_column(default=1, nullable=False)
    upi_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationship to entries
    entries: Mapped[list["RecyclingEntry"]] = relationship("RecyclingEntry", back_populates="user", cascade="all, delete-orphan")




# 5. FastAPI Database Dependency
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 6. Test & Table Initialization Script
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