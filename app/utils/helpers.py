from typing import List, Dict, Any, Optional
import re
from datetime import datetime
from app.utils.logger import logger

def estimate_reading_time(text: str, words_per_minute: int = 200) -> float:
    """Estimate reading time in minutes"""
    word_count = len(text.split())
    return round(word_count / words_per_minute, 1)

def get_word_count(text: str) -> int:
    """Get word count of text"""
    return len(text.split())

def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def extract_urls(text: str) -> List[str]:
    """Extract URLs from text"""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)

def extract_emails(text: str) -> List[str]:
    """Extract email addresses from text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)

def extract_numbers(text: str) -> List[str]:
    """Extract numbers from text"""
    number_pattern = r'\b\d+(?:,\d{3})*(?:\.\d+)?\b'
    return re.findall(number_pattern, text)

def format_text(text: str, width: int = 80) -> str:
    """Format text to specified width"""
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 <= width:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines)

def merge_paragraphs(paragraphs: List[str]) -> str:
    """Merge list of paragraphs into single text"""
    return '\n\n'.join(p.strip() for p in paragraphs if p.strip())

def dict_to_string(data: Dict[str, Any], indent: int = 0) -> str:
    """Convert dictionary to formatted string"""
    lines = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(' ' * indent + f"{key}:")
            lines.append(dict_to_string(value, indent + 2))
        elif isinstance(value, list):
            lines.append(' ' * indent + f"{key}: {str(value)}")
        else:
            lines.append(' ' * indent + f"{key}: {value}")
    return '\n'.join(lines)

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers"""
    try:
        return numerator / denominator if denominator != 0 else default
    except:
        return default

def highlight_text(text: str, keywords: List[str]) -> str:
    """Highlight keywords in text"""
    highlighted = text
    for keyword in keywords:
        pattern = re.compile(f'\\b{re.escape(keyword)}\\b', re.IGNORECASE)
        highlighted = pattern.sub(f'**{keyword}**', highlighted)
    return highlighted

def batch_process(items: List[Any], batch_size: int) -> List[List[Any]]:
    """Split items into batches"""
    batches = []
    for i in range(0, len(items), batch_size):
        batches.append(items[i:i + batch_size])
    return batches
