import re
import string
from typing import List, Dict
from app.utils.logger import logger

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\-\:\;\'\"]', '', text)
    
    return text.strip()

def remove_stop_words(text: str, language: str = "en") -> str:
    """Remove common stop words"""
    import nltk
    from nltk.corpus import stopwords
    
    try:
        stop_words = set(stopwords.words(language))
    except:
        logger.warning(f"Stop words not available for {language}, downloading...")
        nltk.download('stopwords', quiet=True)
        stop_words = set(stopwords.words(language))
    
    words = text.split()
    filtered_words = [w for w in words if w.lower() not in stop_words]
    return ' '.join(filtered_words)

def tokenize(text: str) -> List[str]:
    """Tokenize text into words"""
    return text.lower().split()

def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text"""
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    # Replace tabs with spaces
    text = text.replace('\t', ' ')
    return text.strip()

def remove_punctuation(text: str) -> str:
    """Remove punctuation from text"""
    return text.translate(str.maketrans('', '', string.punctuation))

def lowercase(text: str) -> str:
    """Convert text to lowercase"""
    return text.lower()

def split_sentences(text: str) -> List[str]:
    """Split text into sentences"""
    # Simple sentence splitting
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]

def split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs"""
    return [p.strip() for p in text.split('\n\n') if p.strip()]

def preprocess_text(text: str, 
                   remove_stop_words_flag: bool = False,
                   normalize: bool = True) -> str:
    """Complete preprocessing pipeline"""
    if normalize:
        text = normalize_whitespace(text)
    
    text = clean_text(text)
    
    if remove_stop_words_flag:
        text = remove_stop_words(text)
    
    return text
