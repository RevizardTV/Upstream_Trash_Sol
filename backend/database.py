# backend/database.py
from decimal import Decimal
from typing import Generator
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from backend.config import config

# 1. Determine Database URL
db_url = os.getenv("DATABASE_URL", config.DB_URL)

# SSL Configuration (only applied if not using SQLite)
ssl_args = {}
ca_path = "/etc/ssl/certs/ca-certificates.crt"

if not db_url.startswith("sqlite") and os.path.exists(ca_path):
    ssl_args = {"ssl": {"ca": ca_path}}

# 2. Engine Creation (Use StaticPool for in-memory SQLite to share data across test threads)
is_sqlite_mem = db_url == "sqlite:///:memory:" or db_url == "sqlite://"

connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else ssl_args
pool_class = StaticPool if is_sqlite_mem else None

engine = create_engine(
    db_url,
    connect_args=connect_args,
    poolclass=pool_class,
    pool_pre_ping=True,
)

# 3. Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Database Dependency
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 5. Connection Test & Initialization
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