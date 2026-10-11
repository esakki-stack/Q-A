from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from typing import List, Optional
import os

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra env variables
    )
    
    # Application
    APP_NAME: str = "NewsQAGenerator"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key"
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    HUGGINGFACE_TOKEN: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "sqlite:///./news_qa.db"
    
    # Model Settings
    MODEL_CACHE_DIR: str = "./model_cache"
    DEFAULT_LANGUAGE: str = "en"
    MAX_ARTICLE_LENGTH: int = 10000
    MIN_ARTICLE_LENGTH: int = 500
    
    # Generation Settings
    DEFAULT_QUESTION_COUNT: int = 10
    MAX_QUESTION_COUNT: int = 20
    MIN_CONFIDENCE_THRESHOLD: float = 0.7
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://localhost:8000"])
    
    # File upload - Simple strings instead of JSON lists to avoid parsing issues
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: str = ".txt,.pdf,.docx,.doc"
    
    def get_allowed_file_types(self) -> List[str]:
        """Parse ALLOWED_FILE_TYPES string to list"""
        if isinstance(self.ALLOWED_FILE_TYPES, list):
            return self.ALLOWED_FILE_TYPES
        return [f.strip() for f in self.ALLOWED_FILE_TYPES.split(",")]
    
    def get_cors_origins(self) -> List[str]:
        """Ensure CORS_ORIGINS is a list"""
        if isinstance(self.CORS_ORIGINS, str):
            return [f.strip() for f in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS

# Initialize settings with fallback to defaults if errors occur
try:
    settings = Settings()
except Exception as e:
    print(f"⚠️  Configuration warning: {e}")
    print("   Using default configuration")
    settings = Settings(
        DATABASE_URL="sqlite:///./news_qa.db",
        ALLOWED_FILE_TYPES=".txt,.pdf,.docx,.doc",
        CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
    )

# Create directories if they don't exist
os.makedirs(settings.MODEL_CACHE_DIR, exist_ok=True)
os.makedirs("data/uploads", exist_ok=True)
os.makedirs("data/outputs", exist_ok=True)