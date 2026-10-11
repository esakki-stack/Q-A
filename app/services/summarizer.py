"""Summarizer Service"""
from typing import List, Dict, Any
from app.utils.logger import logger
import re

class ArticleSummarizer:
    """Summarize articles"""
    
    def __init__(self):
        self.default_summary_length = 3
    
    def summarize(self, text: str, max_length: int = 200) -> str:
        """Generate summary of text"""
        try:
            # Split into sentences
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences:
                return "Unable to generate summary."
            
            # Score sentences
            scores = self._score_sentences(sentences, text)
            
            # Get top sentences
            top_sentences = sorted(enumerate(sentences), key=lambda x: scores[x[0]], reverse=True)
            top_sentences = sorted(top_sentences[:self.default_summary_length], key=lambda x: x[0])
            
            summary = '. '.join([s[1] for s in top_sentences]) + '.'
            
            # Truncate if necessary
            while len(summary) > max_length and len(summary.split('.')) > 1:
                sentences_list = summary.split('.')
                sentences_list = sentences_list[:-2]
                summary = '.'.join(sentences_list) + '.'
            
            return summary[:max_length]
        
        except Exception as e:
            logger.error(f"Error summarizing: {str(e)}")
            return "Error generating summary."
    
    @staticmethod
    def _score_sentences(sentences: List[str], text: str) -> List[float]:
        """Score sentences based on importance"""
        scores = []
        
        # Calculate word frequency
        words = text.lower().split()
        word_freq = {}
        
        for word in words:
            word = re.sub(r'[^\w]', '', word)
            if len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Score each sentence
        for sentence in sentences:
            score = 0
            sentence_words = re.sub(r'[^\w\s]', '', sentence.lower()).split()
            
            for word in sentence_words:
                score += word_freq.get(word, 0)
            
            # Normalize by sentence length
            if sentence_words:
                score = score / len(sentence_words)
            
            scores.append(score)
        
        return scores

# Global instance
summarizer = ArticleSummarizer()
