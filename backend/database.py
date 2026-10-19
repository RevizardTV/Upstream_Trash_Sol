from decimal import Decimal
from typing import Generator
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from backend.config import config

# SSL Configuration
ssl_args = {}
ca_path = "/etc/ssl/certs/ca-certificates.crt"

if os.path.exists(ca_path):
    ssl_args = {"ssl": {"ca": ca_path}}

# 1. Engine Creation
engine = create_engine(
    config.DB_URL,
    connect_args=ssl_args,
    pool_pre_ping=True,
)

# 2. Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Database Dependency
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 4. Connection Test & Initialization
def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connection successful! Result:", result.scalar())
    except Exception as e:
        print("❌ Database connection failed!")
        print("Error details:", e)

if __name__ == "__main__":
    from backend.models import Base
    Base.metadata.create_all(bind=engine)
    test_connection()