"""
Database connection setup.
Defaults to SQLite for zero-config local dev (matches database/schema.sql).
To switch to MySQL/Postgres for your Power BI phase, just change DATABASE_URL, e.g.:
    postgresql://user:password@localhost/finguard
    mysql+pymysql://user:password@localhost/finguard
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./finguard.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session, always closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
