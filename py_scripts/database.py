from datetime import datetime, timezone
from typing import Generator, List, Optional
from sqlalchemy import create_engine, text, String, ForeignKey
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
class Base(DeclarativeBase):
    pass

# 4. Database Models
class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
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

    # Bi-directional relationship with RecyclingEntry
    recycling_entries: Mapped[List["RecyclingEntry"]] = relationship("RecyclingEntry", back_populates="user", cascade="all, delete-orphan")


class RecyclingEntry(Base):
    __tablename__ = "recycling_entries"

    entry_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"))
    waste_category: Mapped[str] = mapped_column(String(50))
    weight_kg: Mapped[float]
    payout_amount: Mapped[float]
    entry_type: Mapped[str] = mapped_column(String(20), default="payout")  # "payout" or "charge"
    
    # Relationship back to UserProfile
    user: Mapped["UserProfile"] = relationship("UserProfile", back_populates="recycling_entries")

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