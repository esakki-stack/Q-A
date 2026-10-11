"""
Pydantic Schemas for Request/Response validation
Matches frontend JSON structure for seamless integration
"""

from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class ProcessingStatus(str, Enum):
    """Job processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SourceType(str, Enum):
    """Input source type"""
    TEXT = "text"
    URL = "url"
    PDF = "pdf"
    DOCX = "docx"
    FILE = "file"


class Mode(str, Enum):
    """Generation mode"""
    SIMPLE = "simple"
    IN_DEPTH = "in_depth"
    FAQ = "faq"
    EXPLAINER = "explainer"


class QuestionType(str, Enum):
    """Question type classification"""
    FACTUAL = "factual"
    INFERENTIAL = "inferential"
    ANALYTICAL = "analytical"
    PREDICTIVE = "predictive"
    VOCABULARY = "vocabulary"
    APPLICATION = "application"


class DifficultyLevel(str, Enum):
    """Question difficulty level"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


# ============================================================================
# REQUEST MODELS
# ============================================================================

class QARequest(BaseModel):
    """Q&A generation request"""
    source_type: SourceType = Field(default=SourceType.TEXT, description="Type of input source")
    article_text: Optional[str] = Field(None, description="Raw article text")
    article_url: Optional[HttpUrl] = Field(None, description="URL of article to scrape")
    mode: Mode = Field(default=Mode.SIMPLE, description="Generation mode")
    question_count: int = Field(default=10, ge=1, le=20, description="Number of Q&A pairs to generate")
    language: str = Field(default="en", description="Language code (en, es, fr, etc.)")
    focus_areas: Optional[List[str]] = Field(None, description="Specific topics to focus on")
    exclude_types: Optional[List[QuestionType]] = Field(None, description="Question types to exclude")
    min_confidence: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence threshold")
    
    @field_validator("article_text", mode="before")
    @classmethod
    def validate_article(cls, v, info):
        """Ensure either text or URL is provided"""
        article_text = v
        article_url = info.data.get("article_url")
        
        if not article_text and not article_url:
            raise ValueError("Either article_text or article_url must be provided")
        return v


class BatchQARequest(BaseModel):
    """Batch processing request"""
    articles: List[QARequest] = Field(..., description="List of articles to process")
    batch_size: int = Field(default=5, ge=1, le=20, description="Parallel processing count")


class ProcessingStatusRequest(BaseModel):
    """Check processing status"""
    job_id: str = Field(..., description="Job ID from initial request")


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class QAPair(BaseModel):
    """Single Q&A pair"""
    question: str = Field(..., description="Generated question")
    answer: str = Field(..., description="Extracted answer")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.MEDIUM)
    question_type: QuestionType = Field(default=QuestionType.FACTUAL)
    source_paragraphs: List[int] = Field(default_factory=list, description="Paragraph indices")
    source_text: Optional[str] = Field(None, description="Exact source text reference")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")


class ArticleMetadata(BaseModel):
    """Article metadata extracted"""
    title: Optional[str] = None
    author: Optional[str] = None
    publish_date: Optional[datetime] = None
    source_url: Optional[str] = None
    word_count: int = 0
    reading_time_minutes: float = 0
    language: str = "en"
    categories: List[str] = Field(default_factory=list)


class QAResponse(BaseModel):
    """Complete Q&A generation response"""
    job_id: str = Field(..., description="Unique job identifier")
    status: ProcessingStatus = Field(default=ProcessingStatus.COMPLETED)
    article_metadata: ArticleMetadata
    qa_pairs: List[QAPair]
    summary: Optional[str] = Field(None, description="Auto-generated summary")
    key_entities: Dict[str, List[str]] = Field(default_factory=dict, description="Named entities extracted")
    timeline_events: List[Dict[str, Any]] = Field(default_factory=list, description="Timeline of events")
    stats: Dict[str, Any] = Field(default_factory=dict)
    processing_time: float = Field(..., description="Time taken in seconds")
    mode_used: Mode
    model_version: str = "2.0.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ProcessingStatusResponse(BaseModel):
    """Processing status check response"""
    job_id: str
    status: ProcessingStatus
    progress_percentage: int = Field(ge=0, le=100)
    result: Optional[QAResponse] = None
    error: Optional[str] = None
    created_at: datetime
    estimated_completion: Optional[datetime] = None


class BatchQAResponse(BaseModel):
    """Batch processing response"""
    batch_id: str
    status: ProcessingStatus
    total_articles: int
    processed_count: int
    failed_count: int
    results: List[QAResponse] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    total_time: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    service: str = "NewsQA Generator"
    version: str = "2.0.0"
    database: str = "connected"
    ai_provider: str = "transformers"
    models_loaded: bool
    memory_usage_mb: Optional[float] = None
    uptime_seconds: Optional[float] = None


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    code: str = "INTERNAL_ERROR"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# INTERNAL MODELS (For service communication)
# ============================================================================

class ProcessingJob(BaseModel):
    """Internal processing job model"""
    job_id: str
    status: ProcessingStatus
    source_type: SourceType
    article_text: Optional[str]
    article_url: Optional[str]
    mode: Mode
    question_count: int
    language: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress_percentage: int = 0
    result: Optional[QAResponse] = None
