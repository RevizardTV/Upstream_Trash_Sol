from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import create_engine, text, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from py_scripts.config import config

# 1. Create engine with SSL settings
engine = create_engine(
    config.DB_URL,
    connect_args={"ssl": {"ca": "/etc/ssl/certs/ca-certificates.crt"}},
    pool_pre_ping=True
)

# 2. Modern DeclarativeBase replaces declarative_base()
class Base(DeclarativeBase):
    pass

# 3. Model definition using Mapped[] and mapped_column()
class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    phone_number: Mapped[str] = mapped_column(String(20))
    city: Mapped[str] = mapped_column(String(100))
    postal_code: Mapped[str] = mapped_column(String(20))
    premise_type: Mapped[str] = mapped_column(String(50), default="house")
    household_size: Mapped[int] = mapped_column(default=1)
    
    # Optional typing automatically sets nullable=True
    upi_id: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    
    profile_complete: Mapped[bool] = mapped_column(default=True)
    
    # Timezone-aware UTC timestamp callable
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connection successful! Result:", result.scalar())
    except Exception as e:
        print("❌ Database connection failed!")
        print("Error details:", e)

if __name__ == "__main__":
    # Create tables automatically if they don't exist
    Base.metadata.create_all(bind=engine)
    test_connection()