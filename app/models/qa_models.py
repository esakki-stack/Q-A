"""Pydantic models for QA generation"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"

class QuestionType(str, Enum):
    FACTUAL = "factual"
    INFERENTIAL = "inferential"
    ANALYTICAL = "analytical"
    PREDICTIVE = "predictive"
    VOCABULARY = "vocabulary"
    APPLICATION = "application"

class Mode(str, Enum):
    SIMPLE = "simple"
    IN_DEPTH = "in_depth"
    FAQ = "faq"

class QAPair(BaseModel):
    question: str = Field(..., description="Generated question")
    answer: str = Field(..., description="Extracted answer")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.MEDIUM)
    question_type: QuestionType = Field(default=QuestionType.FACTUAL)
    source_paragraphs: List[int] = Field(default_factory=list)
    source_text: Optional[str] = Field(None, description="Exact source text")
    keywords: List[str] = Field(default_factory=list)
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Confidence must be between 0 and 1')
        return round(v, 3)

class ArticleInfo(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    publish_date: Optional[datetime] = None
    source: Optional[str] = None
    word_count: int = 0
    reading_time_minutes: float = 0
    language: str = "en"
    categories: List[str] = Field(default_factory=list)

class QARequest(BaseModel):
    article_text: Optional[str] = None
    article_url: Optional[str] = None
    mode: Mode = Mode.SIMPLE
    question_count: int = Field(default=10, ge=1, le=20)
    language: str = "en"
    focus_areas: Optional[List[str]] = None
    exclude_types: Optional[List[QuestionType]] = None
    
    @field_validator('article_text', mode='before')
    @classmethod
    def validate_article(cls, v, info):
        # Check if either text or url is provided
        article_text = v
        article_url = info.data.get('article_url')
        
        if not article_text and not article_url:
            raise ValueError('Either article_text or article_url must be provided')
        return v

class QAResponse(BaseModel):
    article_info: ArticleInfo
    qa_pairs: List[QAPair]
    summary: Optional[str] = None
    key_entities: Dict[str, List[str]] = Field(default_factory=dict)
    timeline_events: List[Dict[str, Any]] = Field(default_factory=list)
    stats: Dict[str, Any] = Field(default_factory=dict)
    processing_time: float
    mode_used: Mode
    model_version: str = "1.0.0"
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class BatchRequest(BaseModel):
    articles: List[QARequest]
    batch_size: int = Field(default=5, ge=1, le=20)

class BatchResponse(BaseModel):
    results: List[QAResponse]
    total_processed: int
    failed_count: int
    total_time: float
