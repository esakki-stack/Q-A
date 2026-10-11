"""Answer Extractor Service"""
from typing import List, Dict, Any
from app.utils.logger import logger
import re

class AnswerExtractor:
    """Extract answers from text based on questions"""
    
    def __init__(self):
        self.min_answer_length = 5
        self.max_answer_length = 500
    
    def extract(self, question: str, text: str, sentences: List[str], paragraphs: List[str]) -> Dict[str, Any]:
        """Extract answer for a question from text"""
        try:
            # Score sentences based on relevance to question
            sentence_scores = self._score_sentences(question, sentences)
            
            if not sentence_scores:
                return {
                    "answer": "No relevant information found.",
                    "confidence": 0.0,
                    "source_paragraphs": [],
                    "keywords": []
                }
            
            # Get best matching sentences
            best_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)[:3]
            answer_sentences = [s[0] for s in best_sentences]
            confidence = best_sentences[0][1] if best_sentences else 0.0
            
            # Combine sentences into answer
            answer = ' '.join(answer_sentences).strip()
            
            if not answer:
                answer = "Unable to extract answer."
                confidence = 0.0
            
            # Find source paragraphs
            source_paragraphs = self._find_source_paragraphs(answer_sentences, paragraphs)
            
            # Extract keywords
            keywords = self._extract_keywords(answer)
            
            return {
                "answer": answer,
                "confidence": min(confidence, 1.0),
                "source_paragraphs": source_paragraphs,
                "keywords": keywords
            }
        
        except Exception as e:
            logger.error(f"Error extracting answer: {str(e)}")
            return {
                "answer": "Error extracting answer.",
                "confidence": 0.0,
                "source_paragraphs": [],
                "keywords": []
            }
    
    @staticmethod
    def _score_sentences(question: str, sentences: List[str]) -> List[tuple]:
        """Score sentences based on relevance to question"""
        question_words = set(question.lower().split())
        scored_sentences = []
        
        for sentence in sentences:
            if not sentence.strip():
                continue
            
            sentence_words = set(sentence.lower().split())
            
            # Calculate word overlap
            overlap = len(question_words & sentence_words)
            
            # Calculate relevance score
            score = overlap / len(question_words) if question_words else 0
            
            if score > 0:
                scored_sentences.append((sentence, score))
        
        return scored_sentences
    
    @staticmethod
    def _find_source_paragraphs(sentences: List[str], paragraphs: List[str]) -> List[int]:
        """Find which paragraphs contain the answer sentences"""
        source_paragraphs = []
        
        for sentence in sentences:
            for i, para in enumerate(paragraphs):
                if sentence in para:
                    source_paragraphs.append(i)
        
        return list(set(source_paragraphs))
    
    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction: extract words longer than 4 chars
        words = text.lower().split()
        keywords = [w for w in words if len(w) > 4 and w.isalpha()]
        
        # Remove duplicates
        return list(set(keywords))[:5]

# Global instance
answer_extractor = AnswerExtractor()
