"""
Database Engine and Session Configuration
Supports SQLite (development) and PostgreSQL (production)
"""

from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from logging import getLogger

from app.config import settings

logger = getLogger(__name__)

# Determine database URL
DATABASE_URL = settings.DATABASE_URL
logger.info(f"Database URL: {DATABASE_URL}")

# Engine configuration based on database type
if "sqlite" in DATABASE_URL:
    # SQLite for development - use StaticPool for thread safety
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG,
    )
else:
    # PostgreSQL for production
    engine = create_engine(
        DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # Verify connections before using
    )

# SQLite: Enable foreign keys
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    if "sqlite" in DATABASE_URL:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_db_session() -> Session:
    """Get a database session"""
    return SessionLocal()


from typing import AsyncGenerator

async def get_db() -> AsyncGenerator[Session, None]:
    """Dependency for FastAPI - provides DB session for route handlers"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db():
    """Initialize database tables"""
    from app.database.models import Base
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


def drop_all_tables():
    """Drop all tables (for testing/reset)"""
    from app.database.models import Base
    
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("✅ All tables dropped")
    except Exception as e:
        logger.error(f"❌ Failed to drop tables: {e}")
        raise
