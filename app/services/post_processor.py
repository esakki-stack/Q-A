"""Post-Processor Service"""
from typing import List, Dict, Any
from app.utils.logger import logger
from app.models.qa_models import QAResponse, QAPair

class PostProcessor:
    """Post-process QA results"""
    
    def __init__(self):
        self.min_confidence = 0.5
    
    def process(self, response: QAResponse) -> QAResponse:
        """Post-process QA response"""
        try:
            # Filter by confidence
            filtered_pairs = [p for p in response.qa_pairs if p.confidence >= self.min_confidence]
            response.qa_pairs = filtered_pairs
            
            # Sort by confidence
            response.qa_pairs = sorted(response.qa_pairs, key=lambda x: x.confidence, reverse=True)
            
            logger.info(f"Post-processed {len(response.qa_pairs)} QA pairs")
            return response
        
        except Exception as e:
            logger.error(f"Error in post-processing: {str(e)}")
            return response
    
    @staticmethod
    def filter_by_confidence(qa_pairs: List[QAPair], min_confidence: float = 0.5) -> List[QAPair]:
        """Filter QA pairs by confidence threshold"""
        return [p for p in qa_pairs if p.confidence >= min_confidence]
    
    @staticmethod
    def sort_by_confidence(qa_pairs: List[QAPair]) -> List[QAPair]:
        """Sort QA pairs by confidence"""
        return sorted(qa_pairs, key=lambda x: x.confidence, reverse=True)
    
    @staticmethod
    def deduplicates_questions(qa_pairs: List[QAPair]) -> List[QAPair]:
        """Remove duplicate questions"""
        seen = set()
        unique_pairs = []
        
        for pair in qa_pairs:
            question_hash = hash(pair.question.lower())
            if question_hash not in seen:
                seen.add(question_hash)
                unique_pairs.append(pair)
        
        return unique_pairs

# Global instance
post_processor = PostProcessor()
