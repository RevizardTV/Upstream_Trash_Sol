from __future__ import annotations
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from backend.config import config

ssl_args = {}
ca_path = "/etc/ssl/certs/ca-certificates.crt"
if os.path.exists(ca_path):
    ssl_args = {"ssl": {"ca": ca_path}}

engine = create_engine(
    config.DB_URL,
    connect_args=ssl_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()