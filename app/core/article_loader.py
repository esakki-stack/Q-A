"""Article Loader - Load articles from various sources"""
import logging

try:
    import aiohttp
except ImportError:
    aiohttp = None  # Optional dependency
from typing import Optional, List, Dict, Any
from app.utils.logger import logger
from app.utils.file_handlers import process_uploaded_file
import asyncio

class ArticleLoader:
    """Load articles from URLs, files, or direct text"""
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def load_from_url(self, url: str) -> Dict[str, Any]:
        """Load article from URL"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        text = self._extract_text_from_html(html)
                        return {
                            "text": text,
                            "source": url,
                            "title": self._extract_title_from_html(html)
                        }
                    else:
                        raise Exception(f"HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error loading URL {url}: {str(e)}")
            raise
    
    def load_from_file(self, file_path: str) -> Dict[str, Any]:
        """Load article from file"""
        try:
            text = process_uploaded_file(file_path)
            return {
                "text": text,
                "source": file_path,
                "title": None
            }
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {str(e)}")
            raise
    
    def load_from_text(self, text: str) -> Dict[str, Any]:
        """Load article from direct text"""
        return {
            "text": text,
            "source": "direct_text",
            "title": None
        }
    
    async def load_from_urls_batch(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Load multiple articles from URLs"""
        tasks = [self.load_from_url(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    @staticmethod
    def _extract_text_from_html(html: str) -> str:
        """Extract text from HTML"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator='\n')
            
            # Clean up
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            logger.error(f"Error extracting text from HTML: {str(e)}")
            return html
    
    @staticmethod
    def _extract_title_from_html(html: str) -> Optional[str]:
        """Extract title from HTML"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            title = soup.find('title')
            if title:
                return title.string
            
            h1 = soup.find('h1')
            if h1:
                return h1.get_text()
            
            return None
        except Exception as e:
            logger.error(f"Error extracting title: {str(e)}")
            return None

# Global instance
article_loader = ArticleLoader()
