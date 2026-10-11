"""
AI Provider Interface - Supports multiple LLM backends
Allows seamless switching between OpenAI, Ollama, HuggingFace, Anthropic
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import os
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class AIProvider(str, Enum):
    """Supported AI providers"""
    OPENAI = "openai"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    ANTHROPIC = "anthropic"


class BaseAIProvider(ABC):
    """Abstract base class for AI providers"""

    @abstractmethod
    async def generate_text(
        self, 
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """Generate text from a prompt"""
        pass

    @abstractmethod
    async def generate_questions(
        self,
        text: str,
        num_questions: int = 10,
        question_type: str = "mixed",
    ) -> List[Dict]:
        """Generate Q&A pairs from text"""
        pass

    @abstractmethod
    async def extract_summary(
        self,
        text: str,
        max_length: int = 200,
    ) -> str:
        """Generate summary from text"""
        pass

    @abstractmethod
    async def extract_entities(self, text: str) -> Dict:
        """Extract named entities from text"""
        pass


class OpenAIProvider(BaseAIProvider):
    """OpenAI GPT integration"""

    def __init__(self):
        try:
            import openai
            self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """Generate text using OpenAI"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise

    async def generate_questions(
        self,
        text: str,
        num_questions: int = 10,
        question_type: str = "mixed",
    ) -> List[Dict]:
        """Generate questions using OpenAI"""
        prompt = f"""
Generate {num_questions} insightful questions ({question_type}) for journalism from the following article.
Each question should help readers understand the key points.

Article:
{text[:3000]}

Format your response as a JSON array with objects containing:
- question: The question text
- difficulty: easy, medium, hard, or expert
- type: factual, analytical, or inferential
- related_concept: Main concept being tested

Return ONLY valid JSON array, no markdown formatting.
"""
        response = await self.generate_text(prompt, max_tokens=2000)
        
        try:
            import json
            questions = json.loads(response)
            return questions[:num_questions]
        except json.JSONDecodeError:
            logger.error(f"Failed to parse questions: {response}")
            return []

    async def extract_summary(
        self,
        text: str,
        max_length: int = 200,
    ) -> str:
        """Extract summary using OpenAI"""
        prompt = f"""
Write a concise summary of the following article in exactly {max_length} words or less.
Focus on key facts and main points.

Article:
{text}

Summary:
"""
        return await self.generate_text(prompt, max_tokens=500)

    async def extract_entities(self, text: str) -> Dict:
        """Extract entities using OpenAI"""
        prompt = f"""
Extract named entities from the following article text.
Categorize them as: persons, organizations, locations, dates, events.

Article:
{text[:2000]}

Format response as JSON with these categories.
Return ONLY valid JSON, no markdown.
"""
        response = await self.generate_text(prompt, max_tokens=1000)
        
        try:
            import json
            return json.loads(response)
        except json.JSONDecodeError:
            return {"persons": [], "organizations": [], "locations": []}


class OllamaProvider(BaseAIProvider):
    """Local Ollama LLM integration"""

    def __init__(self):
        try:
            import httpx
            self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            self.model = os.getenv("OLLAMA_MODEL", "mistral")
            self.client = httpx.AsyncClient()
        except ImportError:
            raise ImportError("httpx package not installed. Install with: pip install httpx")

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """Generate text using Ollama"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": temperature,
                },
            )
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise

    async def generate_questions(
        self,
        text: str,
        num_questions: int = 10,
        question_type: str = "mixed",
    ) -> List[Dict]:
        """Generate questions using Ollama"""
        prompt = f"""Generate {num_questions} {question_type} questions for the article below.
Article: {text[:2000]}
Format as JSON array with: question, difficulty, type, related_concept"""
        
        response = await self.generate_text(prompt)
        try:
            import json
            questions = json.loads(response)
            return questions[:num_questions]
        except json.JSONDecodeError:
            return []

    async def extract_summary(
        self,
        text: str,
        max_length: int = 200,
    ) -> str:
        """Extract summary using Ollama"""
        prompt = f"Summarize in {max_length} words: {text}"
        return await self.generate_text(prompt, max_tokens=500)

    async def extract_entities(self, text: str) -> Dict:
        """Extract entities using Ollama"""
        prompt = f"""Extract persons, organizations, locations from: {text[:1500]}
Format as JSON."""
        response = await self.generate_text(prompt)
        try:
            import json
            return json.loads(response)
        except json.JSONDecodeError:
            return {}


class HuggingFaceProvider(BaseAIProvider):
    """HuggingFace transformers integration"""

    def __init__(self):
        try:
            from huggingface_hub import InferenceClient
            api_key = os.getenv("HUGGINGFACE_API_KEY")
            self.client = InferenceClient(api_key=api_key)
            self.model = os.getenv("HUGGINGFACE_MODEL", "mistralai/Mistral-7B-Instruct-v0.1")
        except ImportError:
            raise ImportError("huggingface_hub package not installed. Install with: pip install huggingface_hub")

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """Generate text using HuggingFace"""
        try:
            response = self.client.text_generation(
                prompt,
                model=self.model,
                max_new_tokens=max_tokens,
                temperature=temperature,
            )
            return response
        except Exception as e:
            logger.error(f"HuggingFace error: {e}")
            raise

    async def generate_questions(
        self,
        text: str,
        num_questions: int = 10,
        question_type: str = "mixed",
    ) -> List[Dict]:
        """Generate questions using HuggingFace"""
        prompt = f"""Generate {num_questions} {question_type} questions for this article:
{text[:2000]}
Format as JSON."""
        response = await self.generate_text(prompt)
        try:
            import json
            questions = json.loads(response)
            return questions[:num_questions]
        except json.JSONDecodeError:
            return []

    async def extract_summary(
        self,
        text: str,
        max_length: int = 200,
    ) -> str:
        """Extract summary using HuggingFace"""
        prompt = f"Summarize in {max_length} words:\n{text}"
        return await self.generate_text(prompt, max_tokens=500)

    async def extract_entities(self, text: str) -> Dict:
        """Extract entities using HuggingFace"""
        prompt = f"Extract entities from: {text[:1500]}\nFormat as JSON."
        response = await self.generate_text(prompt)
        try:
            import json
            return json.loads(response)
        except json.JSONDecodeError:
            return {}


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude integration"""

    def __init__(self):
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
        except ImportError:
            raise ImportError("anthropic package not installed. Install with: pip install anthropic")

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """Generate text using Claude"""
        try:
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            raise

    async def generate_questions(
        self,
        text: str,
        num_questions: int = 10,
        question_type: str = "mixed",
    ) -> List[Dict]:
        """Generate questions using Claude"""
        prompt = f"""Generate {num_questions} insightful {question_type} questions for journalists about this article.

Article:
{text[:3000]}

Return a JSON array with objects containing:
- question: The question text
- difficulty: easy, medium, hard, or expert  
- type: factual, analytical, or inferential
- related_concept: Main concept

Return ONLY valid JSON, no markdown."""
        
        response = await self.generate_text(prompt)
        try:
            import json
            questions = json.loads(response)
            return questions[:num_questions]
        except json.JSONDecodeError:
            logger.error(f"Failed to parse questions from Claude")
            return []

    async def extract_summary(
        self,
        text: str,
        max_length: int = 200,
    ) -> str:
        """Extract summary using Claude"""
        prompt = f"""Write a summary of this article in {max_length} words or less.
Focus on the most important information.

Article:
{text}

Summary:"""
        return await self.generate_text(prompt, max_tokens=500)

    async def extract_entities(self, text: str) -> Dict:
        """Extract entities using Claude"""
        prompt = f"""Extract named entities from this text and categorize them.
Categories: persons, organizations, locations, dates, events

Text:
{text[:2000]}

Return as JSON with these category keys."""
        
        response = await self.generate_text(prompt)
        try:
            import json
            return json.loads(response)
        except json.JSONDecodeError:
            return {}


class AIProviderFactory:
    """Factory for creating AI provider instances"""

    _providers = {
        AIProvider.OPENAI: OpenAIProvider,
        AIProvider.OLLAMA: OllamaProvider,
        AIProvider.HUGGINGFACE: HuggingFaceProvider,
        AIProvider.ANTHROPIC: AnthropicProvider,
    }

    @staticmethod
    def get_provider(provider_name: Optional[str] = None) -> BaseAIProvider:
        """Get AI provider instance"""
        provider_name = provider_name or os.getenv("AI_PROVIDER", "openai").lower()
        
        try:
            provider_enum = AIProvider(provider_name)
        except ValueError:
            raise ValueError(f"Unknown AI provider: {provider_name}")

        provider_class = AIProviderFactory._providers.get(provider_enum)
        if not provider_class:
            raise ValueError(f"Provider {provider_name} not configured")

        logger.info(f"Using AI provider: {provider_name}")
        return provider_class()

    @staticmethod
    def register_provider(name: str, provider_class: type):
        """Register custom provider"""
        AIProviderFactory._providers[name] = provider_class


# Singleton instance
_ai_provider = None


async def get_ai_provider() -> BaseAIProvider:
    """Get or create AI provider instance"""
    global _ai_provider
    if _ai_provider is None:
        _ai_provider = AIProviderFactory.get_provider()
    return _ai_provider


async def reset_ai_provider():
    """Reset AI provider (useful for testing)"""
    global _ai_provider
    _ai_provider = None
