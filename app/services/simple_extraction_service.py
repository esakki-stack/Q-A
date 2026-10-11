"""
Simple Extraction Service
Extracts text from various sources without heavy dependencies
"""

import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class SimpleExtractionService:
    """Simple text extraction without external dependencies"""
    
    async def extract(
        self,
        article_text: Optional[str] = None,
        article_url: Optional[str] = None,
    ) -> Tuple[str, dict]:
        """
        Extract article content
        
        Returns:
            Tuple of (extracted_text, metadata)
        """
        try:
            text = article_text or ""
            
            if not text.strip():
                raise ValueError("No text provided")
            
            # Clean up text
            text = self._clean_text(text)
            
            # Extract metadata
            metadata = {
                "title": None,
                "author": None,
                "publish_date": None,
                "source_url": article_url,
                "word_count": len(text.split()),
                "reading_time_minutes": len(text.split()) / 200,
                "language": "en",
                "categories": [],
            }
            
            logger.info(f"✅ Extracted {metadata['word_count']} words")
            
            return text, metadata
            
        except Exception as e:
            logger.error(f"❌ Extraction error: {e}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove extra whitespace
        lines = text.split('\n')
        lines = [l.strip() for l in lines if l.strip()]
        text = '\n'.join(lines)
        
        # Remove URLs
        import re
        text = re.sub(r'http\S+|www\.\S+', '', text)
        
        # Remove extra spaces
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
