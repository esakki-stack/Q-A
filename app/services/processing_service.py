"""
AI Processing Service
Handles question generation, summarization, and extraction using transformers and KeyBERT
Implements singleton pattern for efficient model loading
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import torch
from collections import defaultdict

logger = logging.getLogger(__name__)

# Lazy imports for optional dependencies
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers not installed")

try:
    from keybert import KeyBERT
    KEYBERT_AVAILABLE = True
except ImportError:
    KEYBERT_AVAILABLE = False
    logger.warning("keybert not installed")

try:
    from sumy.parsers.plaintext import PlaintextParser
    try:
        from sumy.nlp.tokenizer import Tokenizer  # type: ignore
    except (ImportError, ModuleNotFoundError):
        Tokenizer = None
    from sumy.summarizers.lsa import LsaSummarizer
    SUMY_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    Tokenizer = None
    SUMY_AVAILABLE = False
    PlaintextParser = None
    LsaSummarizer = None

from app.schemas import QAPair, QAResponse, ArticleMetadata, Mode, QuestionType, DifficultyLevel


class ModelManager:
    """
    Singleton class for managing AI models
    Loads models once at startup and reuses them
    """
    
    _instance = None
    _models = {}
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize model manager"""
        if not self._initialized:
            self._load_models()
            self._initialized = True
    
    def _load_models(self):
        """Load all required models"""
        logger.info("🤖 Loading AI models...")
        
        try:
            if TRANSFORMERS_AVAILABLE:
                # Question generation model
                try:
                    logger.info("  Loading question-generation model...")
                    self._models['qg'] = pipeline(
                        "text2text-generation",
                        model="valhalla/t5-base-qg-hl",
                        device=0 if torch.cuda.is_available() else -1
                    )
                    logger.info("  ✅ Question generation model loaded")
                except Exception as e:
                    logger.warning(f"  ⚠️  Failed to load QG model: {e}")
                
                # Summarization model
                try:
                    logger.info("  Loading summarization model...")
                    self._models['summarization'] = pipeline(
                        "summarization",
                        model="facebook/bart-large-cnn",
                        device=0 if torch.cuda.is_available() else -1
                    )
                    logger.info("  ✅ Summarization model loaded")
                except Exception as e:
                    logger.warning(f"  ⚠️  Failed to load summarization model: {e}")
                
                # Zero-shot classification for question types
                try:
                    logger.info("  Loading classification model...")
                    self._models['classification'] = pipeline(
                        "zero-shot-classification",
                        model="facebook/bart-large-mnli",
                        device=0 if torch.cuda.is_available() else -1
                    )
                    logger.info("  ✅ Classification model loaded")
                except Exception as e:
                    logger.warning(f"  ⚠️  Failed to load classification model: {e}")
            
            if KEYBERT_AVAILABLE:
                try:
                    logger.info("  Loading KeyBERT model...")
                    self._models['keybert'] = KeyBERT(model='distilbert-base-multilingual-cased')
                    logger.info("  ✅ KeyBERT model loaded")
                except Exception as e:
                    logger.warning(f"  ⚠️  Failed to load KeyBERT model: {e}")
            
            if self._models:
                logger.info("✅ Some models loaded successfully")
            else:
                logger.warning("⚠️  No models loaded, running in minimal mode")
            
        except Exception as e:
            logger.error(f"❌ Error loading models: {e}")
            logger.info("  Continuing with degraded functionality")
    
    def get_model(self, model_name: str):
        """Get a specific model"""
        return self._models.get(model_name)
    
    def has_model(self, model_name: str) -> bool:
        """Check if model is loaded"""
        return model_name in self._models


class ProcessingService:
    """
    Main processing service for Q&A generation
    Orchestrates extraction, AI inference, and result formatting
    """
    
    def __init__(self):
        self.model_manager = ModelManager()
        self.question_templates = self._load_question_templates()
    
    @staticmethod
    def _load_question_templates() -> Dict[str, List[str]]:
        """Load question generation templates"""
        return {
            "factual": [
                "What is {topic}?",
                "When did {topic} happen?",
                "Who is {topic}?",
                "Where is {topic} located?",
                "How much {topic}?",
            ],
            "inferential": [
                "Why is {topic} important?",
                "What does this tell us about {topic}?",
                "How does {topic} affect other things?",
                "What can we infer from {topic}?",
            ],
            "analytical": [
                "What are the pros and cons of {topic}?",
                "How does {topic} compare to alternatives?",
                "What is the evidence for {topic}?",
                "How would you evaluate {topic}?",
            ],
            "predictive": [
                "What will happen next with {topic}?",
                "How might {topic} change in the future?",
                "What are the implications of {topic}?",
            ],
        }
    
    async def generate_qa_pairs(
        self,
        article_text: str,
        article_metadata: ArticleMetadata,
        mode: Mode = Mode.SIMPLE,
        question_count: int = 10,
        language: str = "en",
        focus_areas: Optional[List[str]] = None,
        exclude_types: Optional[List[QuestionType]] = None,
    ) -> Tuple[List[QAPair], str, Dict[str, List[str]]]:
        """
        Generate Q&A pairs from article text
        
        Returns:
            Tuple of (qa_pairs, summary, keywords)
        """
        start_time = time.time()
        logger.info(f"🚀 Generating {question_count} Q&A pairs (mode: {mode.value})")
        
        # Split into paragraphs
        paragraphs = [p.strip() for p in article_text.split('\n\n') if p.strip()]
        
        if not paragraphs:
            logger.warning("No valid paragraphs found in article")
            return [], "", {}
        
        # Extract keywords
        keywords = await self._extract_keywords(article_text, language)
        
        # Generate questions
        qa_pairs = await self._generate_questions_async(
            paragraphs,
            question_count,
            mode,
            exclude_types,
            focus_areas,
        )
        
        # Generate summary
        summary = await self._generate_summary(article_text)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Generated {len(qa_pairs)} Q&A pairs in {elapsed:.2f}s")
        
        return qa_pairs, summary, keywords
    
    async def _extract_keywords(
        self,
        text: str,
        language: str = "en",
        top_n: int = 10
    ) -> Dict[str, List[str]]:
        """Extract keywords using KeyBERT"""
        
        try:
            if not self.model_manager.has_model('keybert'):
                logger.warning("KeyBERT model not available")
                return {"keywords": []}
            
            loop = asyncio.get_event_loop()
            keybert = self.model_manager.get_model('keybert')
            
            # Run in executor to avoid blocking
            keywords = await loop.run_in_executor(
                None,
                lambda: keybert.extract_keywords(
                    text,
                    language=language,
                    top_n=top_n,
                    use_maxsum=True,
                    nr_candidates=20
                )
            )
            
            # keywords is list of tuples: [(keyword, score), ...]
            keyword_list = [kw[0] for kw in keywords]
            logger.info(f"🏷️  Extracted keywords: {keyword_list}")
            
            return {"keywords": keyword_list}
            
        except Exception as e:
            logger.error(f"❌ Error extracting keywords: {e}")
            return {"keywords": []}
    
    async def _generate_questions_async(
        self,
        paragraphs: List[str],
        question_count: int,
        mode: Mode,
        exclude_types: Optional[List[QuestionType]] = None,
        focus_areas: Optional[List[str]] = None,
    ) -> List[QAPair]:
        """Generate questions asynchronously"""
        
        qa_pairs = []
        loop = asyncio.get_event_loop()
        
        # Batch process paragraphs
        batch_size = max(1, len(paragraphs) // 4)
        
        for i, paragraph in enumerate(paragraphs[:len(paragraphs)]):
            if len(qa_pairs) >= question_count:
                break
            
            try:
                # Generate question from paragraph
                question = await self._generate_question_from_text(
                    paragraph,
                    mode,
                    focus_areas
                )
                
                if not question:
                    continue
                
                # Determine question type
                q_type = await self._classify_question_type(question, paragraph)
                
                # Skip if excluded
                if exclude_types and q_type in exclude_types:
                    continue
                
                # Determine difficulty
                difficulty = self._estimate_difficulty(question)
                
                qa_pair = QAPair(
                    question=question,
                    answer=paragraph[:500],  # Use first 500 chars as answer
                    confidence=0.75 + (i * 0.01),  # Confidence increases slightly
                    difficulty=difficulty,
                    question_type=q_type,
                    source_paragraphs=[i],
                    source_text=paragraph[:200] + "...",
                    keywords=self._extract_keywords_from_text(paragraph),
                )
                
                qa_pairs.append(qa_pair)
                
            except Exception as e:
                logger.warning(f"⚠️  Error processing paragraph {i}: {e}")
                continue
        
        return qa_pairs[:question_count]
    
    async def _generate_question_from_text(
        self,
        text: str,
        mode: Mode,
        focus_areas: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Generate a single question from text"""
        
        try:
            # Simple question generation from templates for now
            # In production, use actual model
            
            words = text.split()
            if not words:
                return None
            
            # Find key phrase (first 5-10 words)
            key_phrase = " ".join(words[:min(10, len(words))])
            
            # Determine question type based on mode
            if mode == Mode.FAQ:
                template = f"What is the main point about {key_phrase}?"
            elif mode == Mode.EXPLAINER:
                template = f"Can you explain what {key_phrase} means?"
            elif mode == Mode.IN_DEPTH:
                template = f"What are the detailed implications of {key_phrase}?"
            else:  # SIMPLE
                template = f"What does the text say about {key_phrase}?"
            
            return template
            
        except Exception as e:
            logger.warning(f"Error generating question: {e}")
            return None
    
    async def _classify_question_type(
        self,
        question: str,
        context: str
    ) -> QuestionType:
        """Classify question type using zero-shot classification"""
        
        try:
            if not self.model_manager.has_model('classification'):
                return QuestionType.FACTUAL
            
            question_types = [
                "factual", "inferential", "analytical",
                "predictive", "vocabulary", "application"
            ]
            
            classifier = self.model_manager.get_model('classification')
            result = classifier(question, question_types)
            
            top_type = result['labels'][0].lower()
            return QuestionType(top_type)
            
        except Exception as e:
            logger.warning(f"Error classifying question: {e}")
            return QuestionType.FACTUAL
    
    @staticmethod
    def _estimate_difficulty(question: str) -> DifficultyLevel:
        """Estimate question difficulty"""
        
        # Simple heuristic based on question length and words
        words = question.lower().split()
        
        high_difficulty_words = {'how', 'why', 'analyze', 'evaluate', 'compare'}
        difficult_count = sum(1 for w in words if w in high_difficulty_words)
        
        if len(question) < 40:
            return DifficultyLevel.EASY
        elif difficult_count >= 2:
            return DifficultyLevel.HARD
        elif len(question) > 100:
            return DifficultyLevel.EXPERT
        else:
            return DifficultyLevel.MEDIUM
    
    @staticmethod
    def _extract_keywords_from_text(text: str, max_keywords: int = 5) -> List[str]:
        """Extract simple keywords from text"""
        
        # Remove common words
        common_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be',
            'have', 'has', 'do', 'does', 'did', 'will', 'would',
            'should', 'could', 'may', 'might', 'can', 'must',
            'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'it', 'this', 'that'
        }
        
        words = text.lower().split()
        keywords = [w for w in words if w.isalpha() and w not in common_words]
        
        # Return most frequent keywords
        from collections import Counter
        word_counts = Counter(keywords)
        return [w for w, _ in word_counts.most_common(max_keywords)]
    
    async def _generate_summary(self, text: str, max_length: int = 150) -> str:
        """Generate text summary"""
        
        try:
            if not SUMY_AVAILABLE:
                # Simple fallback: first 150 words
                return " ".join(text.split()[:max_length // 5])
            
            parser = PlaintextParser.from_string(text, Tokenizer("english"))
            summarizer = LsaSummarizer()
            summary_sentences = summarizer(parser.document, sentences_count=3)
            
            summary = " ".join([str(s) for s in summary_sentences])
            logger.info(f"📄 Generated summary ({len(summary)} chars)")
            
            return summary[:max_length]
            
        except Exception as e:
            logger.warning(f"Error generating summary: {e}")
            # Fallback: return first 150 words
            return " ".join(text.split()[:max_length // 5])


# Type hints
from typing import Tuple
