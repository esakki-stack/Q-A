"""
Simplified Q&A Generator Service
Generates Q&A pairs from text without external AI dependencies
"""

import asyncio
import logging
import re
from typing import List, Dict, Tuple
import random

logger = logging.getLogger(__name__)


class SimpleQAGenerator:
    """Generate Q&A pairs using simple NLP techniques"""
    
    def __init__(self):
        self.sentence_split_pattern = re.compile(r'[.!?]+')
        self.word_pattern = re.compile(r'\b\w+\b')
    
    async def generate_qa_pairs(
        self,
        text: str,
        question_count: int = 10,
    ) -> List[Dict]:
        """
        Generate Q&A pairs from text
        
        Args:
            text: Article text
            question_count: Number of Q&A pairs to generate
            
        Returns:
            List of Q&A pair dictionaries
        """
        try:
            # Split into sentences
            sentences = self._split_sentences(text)
            
            if not sentences:
                logger.warning("No sentences found in text")
                return []
            
            logger.info(f"📝 Found {len(sentences)} sentences")
            
            # Generate Q&A pairs
            qa_pairs = []
            
            # Strategy 1: Who/What/Where/When/Why questions from key sentences
            key_sentences = sentences[::max(1, len(sentences) // question_count)]
            
            for idx, sentence in enumerate(key_sentences[:question_count]):
                if len(qa_pairs) >= question_count:
                    break
                
                qa_pair = self._generate_qa_from_sentence(sentence, idx)
                if qa_pair:
                    qa_pairs.append(qa_pair)
                
                # Small delay to simulate processing
                await asyncio.sleep(0.05)
            
            # Fill remaining slots if needed
            while len(qa_pairs) < question_count and len(sentences) > 0:
                sentence = random.choice(sentences)
                qa_pair = self._generate_qa_from_sentence(sentence, len(qa_pairs))
                if qa_pair and qa_pair not in qa_pairs:
                    qa_pairs.append(qa_pair)
                if len(qa_pairs) >= question_count:
                    break
            
            logger.info(f"✅ Generated {len(qa_pairs)} Q&A pairs")
            return qa_pairs[:question_count]
            
        except Exception as e:
            logger.error(f"❌ Error generating Q&A: {e}")
            return []
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Split by period, exclamation, question mark
        sentences = re.split(r'[.!?]+', text)
        # Clean and filter
        sentences = [
            s.strip() 
            for s in sentences 
            if s.strip() and len(s.strip()) > 20
        ]
        return sentences
    
    def _generate_qa_from_sentence(self, sentence: str, index: int) -> Dict:
        """Generate a Q&A pair from a sentence"""
        try:
            sentence = sentence.strip()
            
            if not sentence:
                return None
            
            # Extract keywords (first 3-4 significant words)
            words = self.word_pattern.findall(sentence.lower())
            keywords = [w for w in words if len(w) > 3][:3]
            
            # Generate question based on patterns
            question = self._create_question(sentence, keywords, index)
            
            if not question:
                return None
            
            # Answer is the original sentence or part of it
            answer = sentence if len(sentence) < 300 else sentence[:300] + "..."
            
            # Assign confidence
            confidence = 0.65 + (index * 0.03) + random.random() * 0.1
            confidence = min(confidence, 0.95)
            
            return {
                "id": f"qa_{index}",
                "question": question,
                "answer": answer,
                "confidence": confidence,
                "question_type": self._classify_type(question),
                "difficulty": self._estimate_difficulty(sentence),
                "keywords": keywords,
                "source_paragraphs": [index],
                "source_text": sentence[:200],
            }
        except Exception as e:
            logger.warning(f"⚠️  Error generating Q&A from sentence: {e}")
            return None
    
    def _create_question(self, sentence: str, keywords: List[str], index: int) -> str:
        """Create a question from sentence"""
        question_types = [
            # What question
            f"What does the text say about {keywords[0] if keywords else 'this topic'}?",
            
            # How/Why question
            f"How is {keywords[0] if keywords else 'this concept'} described?",
            
            # Definition question
            f"Define {keywords[0] if keywords else 'the main concept'} based on the text.",
            
            # Direct extraction - make a statement into a question
            self._statement_to_question(sentence),
            
            # Comprehension
            f"What is the significance of {keywords[0] if keywords else 'this information'}?",
            
            # Key fact
            f"Identify the key point about {keywords[0] if keywords else 'the topic'} in this text.",
        ]
        
        selected = question_types[index % len(question_types)]
        
        # Clean up
        selected = selected.strip()
        if not selected.endswith('?'):
            selected += '?'
        
        return selected
    
    def _statement_to_question(self, sentence: str) -> str:
        """Convert a statement into a question"""
        sentence = sentence.strip()
        
        # If it's already a question, return it
        if sentence.endswith('?'):
            return sentence
        
        # Try to create inversion for is/are
        if sentence.startswith('The '):
            subject = sentence[4:].split()[0] if len(sentence) > 4 else "subject"
            return f"What can be said about {subject}?"
        
        if ' is ' in sentence or ' are ' in sentence:
            return f"According to the text, {sentence[0].lower()}{sentence[1:]}?"
        
        # Default fallback
        return f"What does the text indicate about {sentence.split()[0]}?" if sentence.split() else "What is the main idea?"
    
    def _classify_type(self, question: str) -> str:
        """Classify question type"""
        q_lower = question.lower()
        
        if q_lower.startswith('what'):
            return 'factual'
        elif q_lower.startswith('why'):
            return 'inferential'
        elif q_lower.startswith('how'):
            return 'analytical'
        elif q_lower.startswith('define'):
            return 'vocabulary'
        else:
            return 'factual'
    
    def _estimate_difficulty(self, text: str) -> str:
        """Estimate question difficulty based on text"""
        word_count = len(text.split())
        
        if word_count < 15:
            return 'easy'
        elif word_count < 25:
            return 'medium'
        elif word_count < 40:
            return 'hard'
        else:
            return 'expert'


async def extract_summary(text: str, max_length: int = 300) -> str:
    """Extract a summary from text"""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return "Summary not available."
    
    # Take first few sentences
    summary = '. '.join(sentences[:min(3, len(sentences))]) + '.'
    
    if len(summary) > max_length:
        summary = summary[:max_length - 3] + '...'
    
    return summary


async def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    """Extract keywords from text"""
    # Simple keyword extraction - use frequent words
    pattern = re.compile(r'\b\w+\b')
    words = pattern.findall(text.lower())
    
    # Filter out common words
    common = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'are', 'was', 'be', 'been', 'as', 'by', 'from', 'it', 'that', 'this', 'with'}
    
    filtered = [w for w in words if w not in common and len(w) > 3]
    
    # Count and get top
    from collections import Counter
    word_freq = Counter(filtered)
    top_keywords = [word for word, _ in word_freq.most_common(top_n)]
    
    return {"keywords": top_keywords}
