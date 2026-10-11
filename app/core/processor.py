"""Main processor pipeline - Enhanced for newsroom Q&A generation"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import time
import os
import json
import logging
from app.utils.logger import logger
from app.models.qa_models import QARequest, QAResponse, ArticleInfo, QAPair, Mode, DifficultyLevel, QuestionType
from app.core.article_loader import article_loader
from app.utils.text_cleaner import split_sentences, split_paragraphs
from app.utils.helpers import get_word_count, estimate_reading_time

# OpenAI Integration
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception:
    openai_client = None

class ArticleProcessor:
    """Main processing pipeline for news article Q&A generation"""
    
    def __init__(self):
        self.use_openai = openai_client is not None and os.getenv("AI_PROVIDER") == "openai"
    
    async def process(self, request: QARequest) -> QAResponse:
        """Process article and generate comprehensive Q&A pairs for newsrooms"""
        start_time = time.time()
        
        try:
            log = logging.getLogger(__name__)
            log.info("Loading article...")
            
            if request.article_url:
                article_data = await article_loader.load_from_url(request.article_url)
            else:
                article_data = article_loader.load_from_text(request.article_text)
            
            article_text = article_data.get("text", request.article_text or "")
            log.info(f"Article loaded, length: {len(article_text)} chars")
            
            # Extract basic article info
            article_info = ArticleInfo(
                title=article_data.get("title", "Untitled"),
                word_count=len(article_text.split()),
                reading_time_minutes=max(1, len(article_text.split()) // 200)
            )
            
            # Generate Q&A pairs using OpenAI or fallback
            log.info(f"Generating {request.question_count} questions...")
            
            if self.use_openai:
                qa_pairs = self._generate_with_openai(article_text, request)
            else:
                qa_pairs = self._generate_simple(article_text, request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Return response
            return QAResponse(
                article_info=article_info,
                qa_pairs=qa_pairs,
                processing_time=processing_time,
                mode_used=request.mode,
                summary="Article processed successfully",
                stats={
                    "total_questions": len(qa_pairs),
                    "average_confidence": sum(p.confidence for p in qa_pairs) / len(qa_pairs) if qa_pairs else 0
                }
            )
            
        except Exception as e:
            log = logging.getLogger(__name__)
            log.error(f"Processing error: {str(e)}", exc_info=True)
            raise
    
    def _generate_with_openai(self, article_text: str, request: QARequest) -> List[QAPair]:
        """Generate Q&A using OpenAI API"""
        log = logging.getLogger(__name__)
        
        try:
            # Create prompt based on mode
            if request.mode == Mode.SIMPLE:
                prompt = f"""Generate {request.question_count} simple, straightforward questions and answers based on this article. 
                
Article:
{article_text}

Please return a JSON array with objects containing "question" and "answer" fields. Make the questions beginner-friendly and answerable from the article."""
            
            elif request.mode == Mode.IN_DEPTH:
                prompt = f"""Generate {request.question_count} in-depth, analytical questions and detailed answers based on this article.

Article:
{article_text}

Please return a JSON array with objects containing "question" and "answer" fields. Make the questions thoughtful and require deeper analysis of the content."""
            
            else:  # FAQ
                prompt = f"""Generate {request.question_count} frequently asked question (FAQ) style questions and concise answers based on this article.

Article:
{article_text}

Please return a JSON array with objects containing "question" and "answer" fields. Format as common FAQs."""
            
            # Call OpenAI API
            response = openai_client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
                messages=[
                    {"role": "system", "content": "You are an expert Q&A generator. Return ONLY valid JSON, no other text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=float(os.getenv("OPENAI_TEMPERATURE", 0.7)),
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", 2000))
            )
            
            # Parse response
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            qa_data = json.loads(response_text)
            
            # Convert to QAPair objects
            qa_pairs = []
            for idx, item in enumerate(qa_data[:request.question_count]):
                qa_pairs.append(QAPair(
                    question=item.get("question", ""),
                    answer=item.get("answer", ""),
                    confidence=0.95,
                    difficulty=DifficultyLevel.MEDIUM,
                    question_type=QuestionType.FACTUAL
                ))
            
            log.info(f"Generated {len(qa_pairs)} Q&A pairs with OpenAI")
            return qa_pairs
            
        except Exception as e:
            log.error(f"OpenAI generation failed: {str(e)}, falling back to simple generation")
            return self._generate_simple(article_text, request)
    
    def _generate_simple(self, article_text: str, request: QARequest) -> List[QAPair]:
        """Fallback simple Q&A generation from sentences"""
        log = logging.getLogger(__name__)
        
        sentences = [s.strip() for s in article_text.split('.') if len(s.strip()) > 20]
        qa_pairs = []
        
        for i, sentence in enumerate(sentences[:request.question_count]):
            qa_pairs.append(QAPair(
                question=f"What about: {sentence[:60]}?",
                answer=sentence,
                confidence=0.8,
                difficulty=DifficultyLevel.MEDIUM,
                question_type=QuestionType.FACTUAL
            ))
        
        log.info(f"Generated {len(qa_pairs)} Q&A pairs with simple method")
        return qa_pairs


# Global instance
article_processor = ArticleProcessor()

