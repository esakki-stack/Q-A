"""Core module initialization"""
from app.core.processor import article_processor
from app.core.article_loader import article_loader

__all__ = ['article_processor', 'article_loader']
