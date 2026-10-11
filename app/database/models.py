"""
Enhanced Database Models - SQLAlchemy ORM for persistent storage
Supports SQLite (dev) and PostgreSQL (prod)
Full user/article/job management with analytics and audit logs
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    create_engine, Column, String, Text, Float, DateTime, Integer, Boolean,
    ForeignKey, Enum as SQLEnum, JSON, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.pool import StaticPool
import uuid
import enum
import os

Base = declarative_base()


class ProcessingStatus(str, enum.Enum):
    """Job processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DifficultyLevel(str, enum.Enum):
    """Question difficulty"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class QuestionType(str, enum.Enum):
    """Question classification"""
    FACTUAL = "factual"
    INFERENTIAL = "inferential"
    ANALYTICAL = "analytical"
    PREDICTIVE = "predictive"
    VOCABULARY = "vocabulary"
    APPLICATION = "application"


class User(Base):
    """User account model"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    articles = relationship("Article", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("ProcessingJob", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"


class APIKey(Base):
    """API key for programmatic access"""
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    key = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey {self.name}>"


class Article(Base):
    """Article storage model"""
    __tablename__ = "articles"
    __table_args__ = (
        Index("idx_user_created", "user_id", "created_at"),
        Index("idx_source_url", "source_url"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String(500), nullable=True, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    source_url = Column(String(500), nullable=True)
    source_name = Column(String(255), nullable=True)
    word_count = Column(Integer, default=0)
    language = Column(String(10), default="en")
    meta_info = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="articles")
    jobs = relationship("ProcessingJob", back_populates="article", cascade="all, delete-orphan")
    entities = relationship("Entity", back_populates="article", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Article {self.id[:8]}>"


class ProcessingJob(Base):
    """Q&A generation job tracking"""
    __tablename__ = "processing_jobs"
    __table_args__ = (
        Index("idx_user_status", "user_id", "status"),
        Index("idx_created", "created_at"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    article_id = Column(String, ForeignKey("articles.id"), nullable=False)
    status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING, index=True)
    mode = Column(String(50), default="in_depth")  # simple, in_depth, faq
    question_count = Column(Integer, default=10)
    error_message = Column(Text, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="jobs")
    article = relationship("Article", back_populates="jobs")
    qa_pairs = relationship("QAPair", back_populates="job", cascade="all, delete-orphan")
    analytics = relationship("JobAnalytics", back_populates="job", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ProcessingJob {self.id[:8]} - {self.status}>"


class QAPair(Base):
    """Generated Q&A pair"""
    __tablename__ = "qa_pairs"
    __table_args__ = (
        Index("idx_job_difficulty", "job_id", "difficulty"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("processing_jobs.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    confidence = Column(Float, default=0.0)
    difficulty = Column(SQLEnum(DifficultyLevel), default=DifficultyLevel.MEDIUM)
    question_type = Column(SQLEnum(QuestionType), default=QuestionType.FACTUAL)
    source_paragraph = Column(Integer, nullable=True)
    source_text = Column(Text, nullable=True)
    keywords = Column(JSON, default=[])
    related_concept = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=False)
    order_position = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("ProcessingJob", back_populates="qa_pairs")

    def __repr__(self):
        return f"<QAPair {self.id[:8]}>"


class Entity(Base):
    """Named entities extracted from articles"""
    __tablename__ = "entities"
    __table_args__ = (
        Index("idx_article_type", "article_id", "entity_type"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    article_id = Column(String, ForeignKey("articles.id"), nullable=False)
    text = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # person, organization, location, etc.
    frequency = Column(Integer, default=1)
    entity_meta = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    article = relationship("Article", back_populates="entities")

    def __repr__(self):
        return f"<Entity {self.text} ({self.entity_type})>"


class JobAnalytics(Base):
    """Analytics and statistics for jobs"""
    __tablename__ = "job_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("processing_jobs.id"), unique=True, nullable=False)
    primary_topic = Column(String(100), nullable=True)
    secondary_topics = Column(JSON, default=[])
    themes = Column(JSON, default=[])
    affected_groups = Column(JSON, default=[])
    time_sensitivity = Column(String(50), nullable=True)
    geographic_scope = Column(String(50), nullable=True)
    tone = Column(String(50), nullable=True)
    sentiment = Column(Float, nullable=True)
    key_entities_count = Column(Integer, default=0)
    timeline_events_count = Column(Integer, default=0)
    average_question_difficulty = Column(String(50), nullable=True)
    readability_score = Column(Float, nullable=True)
    content_score = Column(Float, nullable=True)

    # Relationships
    job = relationship("ProcessingJob", back_populates="analytics")

    def __repr__(self):
        return f"<JobAnalytics {self.job_id[:8]}>"


class ExportLog(Base):
    """Track exports for audit"""
    __tablename__ = "export_logs"
    __table_args__ = (
        Index("idx_job_format", "job_id", "format"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("processing_jobs.id"), nullable=False)
    format = Column(String(50), nullable=False)  # json, markdown, html, csv, pdf
    size_bytes = Column(Integer, nullable=True)
    exported_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<ExportLog {self.job_id[:8]} -> {self.format}>"


# Database initialization
def get_database_url() -> str:
    """Get database URL from environment"""
    url = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    return url


def init_db():
    """Initialize database and create tables"""
    db_url = get_database_url()
    
    # Use check_same_thread for SQLite in development
    if "sqlite" in db_url:
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        engine = create_engine(db_url, pool_pre_ping=True)
    
    Base.metadata.create_all(bind=engine)
    return engine


def get_session_factory():
    """Get session factory"""
    engine = init_db()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Global session factory
SessionLocal = get_session_factory()


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
