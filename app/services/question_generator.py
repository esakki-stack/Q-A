"""Question Generator Service - Reader-Oriented for News Articles"""
from typing import List, Dict, Any
from app.utils.logger import logger
from app.models.qa_models import Mode, QuestionType
import re

class QuestionGenerator:
    """Generate reader-oriented questions from article text"""
    
    def __init__(self):
        self.min_question_length = 10
        self.max_question_length = 200
        
        # Reader-oriented question templates for news articles
        self.question_templates = {
            'what_happened': [
                "What happened?",
                "What is the main event described?",
                "What is the key development in this story?",
                "What are the latest developments?",
            ],
            'why_important': [
                "Why is this issue important?",
                "Why does this matter to the public?",
                "What is the significance of this news?",
                "Why should readers care about this?",
                "How is this relevant to current events?",
            ],
            'who_involved': [
                "Who are the key people involved?",
                "Who are the main stakeholders?",
                "Which organizations or individuals are mentioned?",
                "Who made the decision or announcement?",
                "Who will be affected by this?",
            ],
            'consequences': [
                "What are the consequences?",
                "What impact will this have?",
                "What are the potential outcomes?",
                "How does this affect the public?",
                "What are the long-term implications?",
            ],
            'what_next': [
                "What happens next?",
                "What are the next steps?",
                "How will this situation develop?",
                "What is expected to happen?",
                "What are the pending actions?",
            ],
            'public_impact': [
                "How does this impact the public?",
                "How will this affect ordinary people?",
                "What changes can readers expect?",
                "How does this influence society?",
            ]
        }
    
    def generate(self, text: str, num_questions: int = 10, mode: Mode = Mode.SIMPLE, difficulty: str = "medium") -> List[Dict[str, Any]]:
        """Generate reader-oriented questions from text"""
        try:
            if mode == Mode.SIMPLE:
                return self._generate_simple_questions(text, num_questions, difficulty)
            elif mode == Mode.IN_DEPTH:
                return self._generate_in_depth_questions(text, num_questions, difficulty)
            elif mode == Mode.FAQ:
                return self._generate_faq_questions(text, num_questions, difficulty)
            else:
                return self._generate_simple_questions(text, num_questions, difficulty)
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            return []
    
    def _generate_simple_questions(self, text: str, num_questions: int, difficulty: str = "medium") -> List[Dict[str, Any]]:
        """Generate simple, reader-friendly questions covering key information"""
        questions = []
        
        # Distribute questions across key question types
        question_types = ['what_happened', 'why_important', 'who_involved', 'consequences', 'what_next', 'public_impact']
        questions_per_type = max(1, num_questions // len(question_types))
        
        for q_type in question_types:
            if len(questions) >= num_questions:
                break
            
            templates = self.question_templates.get(q_type, [])
            for template in templates[:questions_per_type]:
                if len(questions) >= num_questions:
                    break
                
                question_dict = {
                    'question': template,
                    'type': q_type,
                    'difficulty': difficulty,
                    'question_type': self._map_type_to_enum(q_type)
                }
                questions.append(question_dict)
        
        # Fill remaining slots with custom questions from text
        if len(questions) < num_questions:
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip() and len(s.split()) > 5]
            
            for sentence in sentences:
                if len(questions) >= num_questions:
                    break
                question = self._statement_to_question(sentence)
                if question and self.min_question_length <= len(question) <= self.max_question_length:
                    questions.append({
                        'question': question,
                        'type': 'factual',
                        'difficulty': difficulty,
                        'question_type': 'FACTUAL'
                    })
        
        return questions[:num_questions]
    
    def _generate_in_depth_questions(self, text: str, num_questions: int, difficulty: str = "hard") -> List[Dict[str, Any]]:
        """Generate in-depth analytical questions"""
        questions = []
        
        # Extract key phrases and entities
        key_phrases = self._extract_key_phrases(text)
        
        analytical_templates = [
            "What are the underlying factors behind {}?",
            "How does {} connect to broader trends?",
            "What are the implications of {} for the future?",
            "How can we analyze the impact of {}?",
            "What evidence supports claims about {}?",
            "How does {} relate to similar situations?",
            "What are the different perspectives on {}?",
            "How might {} evolve in the coming months?",
        ]
        
        question_count = 0
        for phrase in key_phrases:
            if question_count >= num_questions:
                break
            
            for template in analytical_templates:
                if question_count >= num_questions:
                    break
                
                question_text = template.format(phrase)
                questions.append({
                    'question': question_text,
                    'type': 'analytical',
                    'difficulty': difficulty,
                    'question_type': 'ANALYTICAL',
                    'related_concept': phrase
                })
                question_count += 1
        
        return questions[:num_questions]
    
    def _generate_faq_questions(self, text: str, num_questions: int, difficulty: str = "easy") -> List[Dict[str, Any]]:
        """Generate FAQ-style questions optimized for newsroom explainers"""
        faq_templates = [
            {
                'question': "What is this article about?",
                'type': 'what_happened',
                'question_type': 'FACTUAL'
            },
            {
                'question': "Who are the key people or organizations involved?",
                'type': 'who_involved',
                'question_type': 'FACTUAL'
            },
            {
                'question': "Why is this important right now?",
                'type': 'why_important',
                'question_type': 'INFERENTIAL'
            },
            {
                'question': "What are the main consequences or impacts?",
                'type': 'consequences',
                'question_type': 'INFERENTIAL'
            },
            {
                'question': "What will happen next?",
                'type': 'what_next',
                'question_type': 'PREDICTIVE'
            },
            {
                'question': "How does this affect me?",
                'type': 'public_impact',
                'question_type': 'APPLICATION'
            },
            {
                'question': "What is the timeline of events?",
                'type': 'timeline',
                'question_type': 'FACTUAL'
            },
            {
                'question': "Are there different viewpoints on this issue?",
                'type': 'perspectives',
                'question_type': 'ANALYTICAL'
            },
        ]
        
        questions = []
        for faq in faq_templates[:num_questions]:
            questions.append({
                'question': faq['question'],
                'type': faq['type'],
                'difficulty': difficulty,
                'question_type': faq['question_type']
            })
        
        return questions[:num_questions]
    
    def _map_type_to_enum(self, type_str: str) -> str:
        """Map question type string to QuestionType enum"""
        mapping = {
            'what_happened': 'FACTUAL',
            'why_important': 'INFERENTIAL',
            'who_involved': 'FACTUAL',
            'consequences': 'INFERENTIAL',
            'what_next': 'PREDICTIVE',
            'public_impact': 'APPLICATION',
            'factual': 'FACTUAL',
            'analytical': 'ANALYTICAL',
            'timeline': 'FACTUAL',
            'perspectives': 'ANALYTICAL'
        }
        return mapping.get(type_str, 'FACTUAL')
    
    @staticmethod
    def _extract_key_phrases(text: str) -> List[str]:
        """Extract key phrases from text"""
        # Simple extraction based on capital words and phrases
        sentences = re.split(r'[.!?]+', text)
        phrases = []
        
        for sentence in sentences[:5]:  # Focus on first 5 sentences
            # Find capitalized phrases
            caps_phrases = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?', sentence)
            phrases.extend(caps_phrases)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_phrases = []
        for phrase in phrases:
            if phrase.lower() not in seen and len(phrase.split()) <= 3:
                unique_phrases.append(phrase)
                seen.add(phrase.lower())
        
        return unique_phrases[:15]
    
    @staticmethod
    def _statement_to_question(statement: str) -> str:
        """Convert a statement to a question"""
        statement = statement.strip()
        statement = re.sub(r'[.!?]+$', '', statement)
        
        if not statement or len(statement.split()) < 3:
            return ""
        
        words = statement.split()
        
        # Simple conversion: capitalize and add question mark
        return statement.capitalize() + "?"
    
    @staticmethod
    def _extract_key_phrases(text: str) -> List[str]:
        """Extract key phrases from text"""
        # Simple implementation: extract noun phrases
        phrases = []
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of'}
        
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            words = sentence.split()
            phrase = []
            
            for word in words:
                if word.lower() not in stop_words and len(word) > 2:
                    phrase.append(word)
                elif phrase:
                    phrases.append(' '.join(phrase))
                    phrase = []
            
            if phrase:
                phrases.append(' '.join(phrase))
        
        # Remove duplicates and return unique phrases
        return list(set(phrases))[:10]

# Global instance
question_generator = QuestionGenerator()
