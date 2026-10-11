"""
Article Loader Module
Handles loading articles from various sources: URLs, files, text, APIs
"""

import re
import asyncio
import aiohttp
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse
import tempfile
import os
from datetime import datetime
import hashlib

from app.config import settings
from app.utils.logger import logger
from app.utils.file_handlers import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_doc
)

class ArticleLoader:
    """
    Load articles from various sources with caching and error handling
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache_dir = "data/cache/articles"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Domain-specific parsers (extendable)
        self.domain_parsers = {
            "nytimes.com": self._parse_nytimes,
            "bbc.com": self._parse_bbc,
            "reuters.com": self._parse_reuters,
            "theguardian.com": self._parse_guardian,
            "indianexpress.com": self._parse_indian_express,
            "timesofindia.indiatimes.com": self._parse_toi,
            # Add more as needed
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def initialize(self):
        """Initialize HTTP session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def load_from_url(self, url: str, use_cache: bool = True) -> str:
        """
        Load article from URL with intelligent parsing
        
        Args:
            url: Article URL
            use_cache: Use cached version if available
        
        Returns:
            Extracted article text
        """
        try:
            # Validate URL
            if not self._is_valid_url(url):
                raise ValueError(f"Invalid URL: {url}")
            
            # Check cache
            cache_key = self._generate_cache_key(url)
            cache_path = os.path.join(self.cache_dir, f"{cache_key}.txt")
            
            if use_cache and os.path.exists(cache_path):
                logger.info(f"Loading from cache: {url}")
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            # Fetch from URL
            logger.info(f"Fetching article from URL: {url}")
            
            await self.initialize()
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                              '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    raise ValueError(f"HTTP {response.status}: Failed to fetch URL")
                
                content_type = response.headers.get('content-type', '')
                html = await response.text()
            
            # Parse HTML based on domain
            article_text = self._parse_html(html, url)
            
            # Clean and validate text
            article_text = self._clean_article_text(article_text)
            
            # Cache the result
            if use_cache:
                with open(cache_path, 'w', encoding='utf-8') as f:
                    f.write(article_text)
            
            logger.info(f"Successfully loaded article from URL: {url}")
            logger.info(f"Article length: {len(article_text)} characters")
            
            return article_text
            
        except Exception as e:
            logger.error(f"Error loading from URL {url}: {e}")
            # Fallback to newspaper3k if available
            try:
                return await self._fallback_newspaper3k(url)
            except:
                raise ValueError(f"Failed to load article from URL: {str(e)}")
    
    async def load_from_file(self, file_path: str, file_type: str = None) -> str:
        """
        Load article from file (PDF, DOCX, DOC, TXT)
        
        Args:
            file_path: Path to file
            file_type: File type (auto-detected if None)
        
        Returns:
            Extracted text
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Determine file type from extension
            if not file_type:
                _, ext = os.path.splitext(file_path)
                file_type = ext.lower()
            
            logger.info(f"Loading article from file: {file_path} ({file_type})")
            
            # Extract text based on file type
            if file_type == '.pdf':
                text = extract_text_from_pdf(file_path)
            elif file_type in ['.docx', '.doc']:
                text = extract_text_from_docx(file_path)
            elif file_type == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            # Clean text
            text = self._clean_article_text(text)
            
            logger.info(f"Successfully loaded article from file: {file_path}")
            logger.info(f"Article length: {len(text)} characters")
            
            return text
            
        except Exception as e:
            logger.error(f"Error loading from file {file_path}: {e}")
            raise ValueError(f"Failed to load article from file: {str(e)}")
    
    def load_from_text(self, text: str) -> str:
        """
        Load article from direct text input
        
        Args:
            text: Article text
        
        Returns:
            Cleaned article text
        """
        try:
            if not text or len(text.strip()) < settings.MIN_ARTICLE_LENGTH:
                raise ValueError(
                    f"Article text too short. Minimum {settings.MIN_ARTICLE_LENGTH} characters required."
                )
            
            if len(text) > settings.MAX_ARTICLE_LENGTH:
                text = text[:settings.MAX_ARTICLE_LENGTH]
                logger.warning(f"Article truncated to {settings.MAX_ARTICLE_LENGTH} characters")
            
            # Clean text
            cleaned_text = self._clean_article_text(text)
            
            logger.info(f"Loaded article from text input")
            logger.info(f"Article length: {len(cleaned_text)} characters")
            
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Error loading from text: {e}")
            raise ValueError(f"Failed to load article from text: {str(e)}")
    
    async def load_from_news_api(self, query: str, language: str = 'en') -> List[Dict[str, Any]]:
        """
        Load articles from News API (requires API key)
        
        Args:
            query: Search query
            language: Language code
        
        Returns:
            List of articles with metadata
        """
        if not settings.NEWS_API_KEY:
            raise ValueError("News API key not configured")
        
        try:
            await self.initialize()
            
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'language': language,
                'apiKey': settings.NEWS_API_KEY,
                'pageSize': 10,
                'sortBy': 'relevancy'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    raise ValueError(f"News API error: {response.status}")
                
                data = await response.json()
            
            articles = []
            for item in data.get('articles', []):
                try:
                    article_text = await self.load_from_url(item['url'], use_cache=True)
                    articles.append({
                        'title': item.get('title', ''),
                        'author': item.get('author', ''),
                        'source': item.get('source', {}).get('name', ''),
                        'published_at': item.get('publishedAt', ''),
                        'url': item.get('url', ''),
                        'text': article_text
                    })
                except Exception as e:
                    logger.warning(f"Failed to load article {item['url']}: {e}")
                    continue
            
            return articles
            
        except Exception as e:
            logger.error(f"Error loading from News API: {e}")
            return []
    
    async def batch_load_urls(self, urls: List[str], max_concurrent: int = 5) -> Dict[str, str]:
        """
        Load multiple articles concurrently
        
        Args:
            urls: List of URLs
            max_concurrent: Maximum concurrent requests
        
        Returns:
            Dictionary of URL -> article text
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}
        
        async def load_with_semaphore(url):
            async with semaphore:
                try:
                    text = await self.load_from_url(url)
                    return url, text
                except Exception as e:
                    logger.error(f"Failed to load {url}: {e}")
                    return url, None
        
        tasks = [load_with_semaphore(url) for url in urls]
        completed = await asyncio.gather(*tasks)
        
        for url, text in completed:
            if text:
                results[url] = text
        
        return results
    
    def _parse_html(self, html: str, url: str) -> str:
        """
        Parse HTML to extract article text
        Uses domain-specific parsers when available
        """
        try:
            # Try domain-specific parser
            domain = self._extract_domain(url)
            if domain in self.domain_parsers:
                return self.domain_parsers[domain](html)
            
            # Fallback to generic parser
            return self._parse_generic(html)
            
        except Exception as e:
            logger.warning(f"Error in HTML parsing for {url}: {e}")
            return self._parse_generic(html)
    
    def _parse_generic(self, html: str) -> str:
        """Generic HTML parser using regex patterns"""
        # Remove scripts and styles
        html = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Extract article content (common patterns)
        article_patterns = [
            r'<article[^>]*>(.*?)</article>',
            r'<div[^>]*class="[^"]*article[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*id="[^"]*content[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*post[^"]*"[^>]*>(.*?)</div>',
        ]
        
        for pattern in article_patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            if matches:
                content = ' '.join(matches)
                break
        else:
            # If no specific pattern matches, use body
            body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
            content = body_match.group(1) if body_match else html
        
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', ' ', content)
        
        # Decode HTML entities
        import html as html_module
        content = html_module.unescape(content)
        
        # Clean whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content
    
    def _parse_nytimes(self, html: str) -> str:
        """New York Times specific parser"""
        # NYTimes specific selectors
        patterns = [
            r'<article[^>]*>(.*?)</article>',
            r'<section[^>]*name="articleBody"[^>]*>(.*?)</section>',
            r'<div[^>]*class="StoryBodyCompanionColumn"[^>]*>(.*?)</div>',
        ]
        
        return self._extract_with_patterns(html, patterns)
    
    def _parse_bbc(self, html: str) -> str:
        """BBC specific parser"""
        patterns = [
            r'<article[^>]*>(.*?)</article>',
            r'<div[^>]*data-component="text-block"[^>]*>(.*?)</div>',
            r'<div[^>]*class="ssrcss-uf6wea-RichTextComponentWrapper"[^>]*>(.*?)</div>',
        ]
        
        return self._extract_with_patterns(html, patterns)
    
    def _parse_reuters(self, html: str) -> str:
        """Reuters specific parser"""
        patterns = [
            r'<article[^>]*>(.*?)</article>',
            r'<div[^>]*class="ArticleBody__content"[^>]*>(.*?)</div>',
            r'<div[^>]*data-testid="paragraph"[^>]*>(.*?)</div>',
        ]
        
        return self._extract_with_patterns(html, patterns)
    
    def _parse_guardian(self, html: str) -> str:
        """The Guardian specific parser"""
        patterns = [
            r'<div[^>]*id="maincontent"[^>]*>(.*?)</div>',
            r'<div[^>]*class="article-body-commercial-selector"[^>]*>(.*?)</div>',
        ]
        
        return self._extract_with_patterns(html, patterns)
    
    def _parse_indian_express(self, html: str) -> str:
        """Indian Express specific parser"""
        patterns = [
            r'<div[^>]*class="story-details"[^>]*>(.*?)</div>',
            r'<div[^>]*id="story_content"[^>]*>(.*?)</div>',
        ]
        
        return self._extract_with_patterns(html, patterns)
    
    def _parse_toi(self, html: str) -> str:
        """Times of India specific parser"""
        patterns = [
            r'<div[^>]*class="_s30J clearfix"[^>]*>(.*?)</div>',
            r'<div[^>]*class="article_content"[^>]*>(.*?)</div>',
        ]
        
        return self._extract_with_patterns(html, patterns)
    
    def _extract_with_patterns(self, html: str, patterns: List[str]) -> str:
        """Extract content using multiple patterns"""
        content_parts = []
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            for match in matches:
                # Remove HTML tags from the match
                clean_text = re.sub(r'<[^>]+>', ' ', match)
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                if clean_text and len(clean_text) > 100:  # Ensure meaningful content
                    content_parts.append(clean_text)
        
        if content_parts:
            return ' '.join(content_parts)
        
        # Fallback to generic parser
        return self._parse_generic(html)
    
    def _clean_article_text(self, text: str) -> str:
        """
        Clean and normalize article text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:\'\"-()]', ' ', text)
        
        # Remove multiple periods
        text = re.sub(r'\.{2,}', '.', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Ensure proper sentence spacing
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        text = re.sub(r'([.,!?;:])(\w)', r'\1 \2', text)
        
        # Capitalize first letter
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        
        return text
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme in ['http', 'https'], result.netloc])
        except:
            return False
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            return urlparse(url).netloc
        except:
            return ""
    
    def _generate_cache_key(self, url: str) -> str:
        """Generate cache key from URL"""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:16]
        domain = self._extract_domain(url).replace('.', '_')
        return f"{domain}_{url_hash}"
    
    async def _fallback_newspaper3k(self, url: str) -> str:
        """
        Fallback to newspaper3k library if available
        """
        try:
            import newspaper
            from newspaper import Article
            
            article = Article(url)
            article.download()
            article.parse()
            
            text = article.text
            if not text:
                raise ValueError("No text extracted")
            
            return self._clean_article_text(text)
            
        except ImportError:
            raise ValueError("Newspaper3k not installed. Install with: pip install newspaper3k")
        except Exception as e:
            raise ValueError(f"Newspaper3k failed: {str(e)}")
    
    def extract_metadata(self, text: str, url: str = None) -> Dict[str, Any]:
        """
        Extract metadata from article text
        """
        metadata = {
            'title': '',
            'estimated_reading_time': 0,
            'word_count': 0,
            'sentence_count': 0,
            'paragraph_count': 0,
            'source': url if url else 'text_input',
            'extracted_at': datetime.now().isoformat(),
            'language': self._detect_language(text)
        }
        
        # Extract title (first line or first 100 chars)
        lines = text.strip().split('\n')
        if lines:
            metadata['title'] = lines[0][:200]
        
        # Calculate statistics
        words = text.split()
        metadata['word_count'] = len(words)
        metadata['estimated_reading_time'] = len(words) / 200  # 200 WPM
        
        # Count sentences and paragraphs
        sentences = re.split(r'[.!?]+', text)
        metadata['sentence_count'] = len([s for s in sentences if s.strip()])
        metadata['paragraph_count'] = len(text.split('\n\n'))
        
        # Extract potential author (common patterns)
        author_patterns = [
            r'By\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'Written by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'Author:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata['author'] = match.group(1).strip()
                break
        
        return metadata
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection (basic implementation)"""
        # Simple English detection
        english_words = ['the', 'and', 'of', 'to', 'in', 'is', 'that', 'for', 'it', 'as']
        text_lower = text.lower()
        
        english_count = sum(1 for word in english_words if word in text_lower)
        
        if english_count >= 3:
            return 'en'
        
        # Add more language detection as needed
        return 'unknown'


# Singleton instance for easy access
article_loader = ArticleLoader()

# Convenience functions
async def load_article(url: str = None, text: str = None, file_path: str = None) -> Tuple[str, Dict[str, Any]]:
    """
    Convenience function to load article from any source
    
    Returns:
        Tuple of (article_text, metadata)
    """
    loader = ArticleLoader()
    
    try:
        if url:
            article_text = await loader.load_from_url(url)
            metadata = loader.extract_metadata(article_text, url)
        elif file_path:
            article_text = await loader.load_from_file(file_path)
            metadata = loader.extract_metadata(article_text, file_path)
        elif text:
            article_text = loader.load_from_text(text)
            metadata = loader.extract_metadata(article_text)
        else:
            raise ValueError("Must provide url, text, or file_path")
        
        return article_text, metadata
        
    finally:
        await loader.close()


# Test function
async def test_article_loader():
    """Test the article loader with sample URLs"""
    test_urls = [
        "https://www.bbc.com/news/world-us-canada-67823456",
        "https://www.reuters.com/business/environment/2024",
        "https://indianexpress.com/article/india/",
    ]
    
    async with ArticleLoader() as loader:
        for url in test_urls:
            try:
                print(f"\nLoading: {url}")
                text = await loader.load_from_url(url)
                metadata = loader.extract_metadata(text, url)
                
                print(f"Title: {metadata['title'][:100]}...")
                print(f"Word count: {metadata['word_count']}")
                print(f"Reading time: {metadata['estimated_reading_time']:.1f} minutes")
                print(f"Preview: {text[:200]}...")
                
            except Exception as e:
                print(f"Failed to load {url}: {e}")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_article_loader())