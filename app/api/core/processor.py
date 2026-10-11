from typing import Dict, Any, Optional
from app.models.qa_models import QARequest, QAResponse, ArticleInfo, QAPair, Mode
from app.services.question_generator import question_generator
from app.services.answer_extractor import answer_extractor
from app.services.entity_extractor import EntityExtractor
from app.services.summarizer import ArticleSummarizer
from app.core.article_loader import ArticleLoader
from app.utils.logger import logger
import time

class ArticleProcessor:
    def __init__(self):
        self.article_loader = ArticleLoader()
        self.entity_extractor = EntityExtractor()
        self.summarizer = ArticleSummarizer()
        logger.info("ArticleProcessor initialized")
    
    async def process_article(self, request: QARequest) -> QAResponse:
        """Main processing pipeline"""
        start_time = time.time()
        
        try:
            logger.info(f"Processing article request in {request.mode} mode")
            
            # Step 1: Load article text
            article_text = await self._load_article(request)
            if not article_text:
                raise ValueError("Failed to load article text")
            
            # Step 2: Extract article information
            article_info = self._extract_article_info(article_text, request)
            
            # Step 3: Generate questions based on mode
            if request.mode == Mode.FAQ:
                question_data = question_generator.generate_faq_questions(
                    article_text, 
                    request.question_count
                )
            else:
                question_data = question_generator.generate_from_text(
                    article_text, 
                    request.question_count
                )
            
            # Step 4: Extract answers for each question
            qa_pairs = []
            for q_data in question_data:
                answer_data = answer_extractor.extract_answer(
                    q_data["question"],
                    article_text
                )
                
                qa_pair = QAPair(
                    question=q_data["question"],
                    answer=answer_data["answer"],
                    confidence=answer_data["confidence"],
                    difficulty=q_data.get("difficulty"),
                    question_type=q_data.get("question_type"),
                    source_paragraphs=[],  # Would need paragraph mapping
                    keywords=q_data.get("keywords", [])
                )
                qa_pairs.append(qa_pair)
            
            # Step 5: Generate summary
            summary = self.summarizer.summarize(article_text)
            
            # Step 6: Extract entities
            entities = self.entity_extractor.extract_entities(article_text)
            
            # Step 7: Calculate processing time
            processing_time = time.time() - start_time
            
            # Step 8: Prepare response
            response = QAResponse(
                article_info=article_info,
                qa_pairs=qa_pairs,
                summary=summary,
                key_entities=entities,
                timeline_events=[],  # Would need timeline extraction
                stats={
                    "total_questions": len(qa_pairs),
                    "avg_confidence": sum(q.confidence for q in qa_pairs) / len(qa_pairs) if qa_pairs else 0,
                    "article_length": len(article_text.split()),
                    "processing_speed": len(article_text) / processing_time if processing_time > 0 else 0
                },
                processing_time=processing_time,
                mode_used=request.mode
            )
            
            logger.info(f"Article processed successfully in {processing_time:.2f} seconds")
            return response
            
        except Exception as e:
            logger.error(f"Error processing article: {e}")
            raise
    
    async def _load_article(self, request: QARequest) -> Optional[str]:
        """Load article from text or URL"""
        if request.article_text:
            return request.article_text
        elif request.article_url:
            return await self.article_loader.load_from_url(request.article_url)
        return None
    
    def _extract_article_info(self, text: str, request: QARequest) -> ArticleInfo:
        """Extract basic article information"""
        words = text.split()
        word_count = len(words)
        reading_time = word_count / 200  # Average reading speed
        
        # Extract title (first line or first 100 chars)
        lines = text.strip().split('\n')
        title = lines[0][:100] if lines else "Untitled Article"
        
        return ArticleInfo(
            title=title,
            word_count=word_count,
            reading_time_minutes=reading_time,
            language=request.language,
            categories=["general"]  # Would need category classification
        )
    
    def process_batch(self, requests: list) -> list:
        """Process multiple articles in batch"""
        results = []
        for request in requests:
            try:
                result = self.process_article(request)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process request: {e}")
                results.append(None)
        return results

# Global instance
article_processor = ArticleProcessor()