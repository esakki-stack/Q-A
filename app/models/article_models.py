"""Article models for database"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ArticleCategory(str, Enum):
    POLITICS = "politics"
    BUSINESS = "business"
    TECHNOLOGY = "technology"
    SCIENCE = "science"
    HEALTH = "health"
    SPORTS = "sports"
    ENTERTAINMENT = "entertainment"
    WORLD = "world"
    NATIONAL = "national"
    LOCAL = "local"
    OPINION = "opinion"
    ANALYSIS = "analysis"
    INVESTIGATIVE = "investigative"
    FEATURE = "feature"
    BREAKING = "breaking"
    OTHER = "other"

class ArticleSource(str, Enum):
    URL = "url"
    FILE = "file"
    TEXT = "text"
    API = "api"
    DATABASE = "database"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"

class Language(str, Enum):
    ENGLISH = "en"
    HINDI = "hi"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    TAMIL = "ta"
    TELUGU = "te"
    KANNADA = "kn"
    MALAYALAM = "ml"
    OTHER = "other"

class ArticleCreate(BaseModel):
    title: Optional[str] = None
    content: str
    author: Optional[str] = None
    source_url: Optional[str] = None
    source_domain: Optional[str] = None
    category: ArticleCategory = ArticleCategory.OTHER
    language: Language = Language.ENGLISH

class ArticleResponse(BaseModel):
    id: str
    title: Optional[str]
    content: str
    summary: Optional[str]
    author: Optional[str]
    source_url: Optional[str]
    word_count: int
    processing_status: ProcessingStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
