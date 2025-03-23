"""
Service for summarizing content using various LLM providers.
"""

import logging
import json
import time
from typing import Dict, Any, Optional, List
import requests
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate_summary(self, story: Dict[str, Any], content: Dict[str, Any]) -> str:
        """Generate a summary using the LLM provider."""
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini API provider for summarization."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash-latest",
        max_tokens: int = 500,
    ):
        """
        Initialize the Gemini provider.

        Args:
            api_key: Google API key
            model: Model to use (default: gemini-1.5-flash-latest)
            max_tokens: Maximum tokens for the summary
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens

        # Log the model being used
        logger.info(f"Initializing Gemini provider with model: {model}")

        # Import here to avoid requiring the package if not using Gemini
        try:
            import google.generativeai as genai

            self.genai = genai
            self.genai.configure(api_key=self.api_key)
        except ImportError:
            logger.error("google-generativeai package not installed. Install with: pip install google-generativeai")
            raise

    def generate_summary(self, story: Dict[str, Any], content: Dict[str, Any]) -> str:
        """
        Generate a summary using Google Gemini.

        Args:
            story: Story metadata from Hacker News
            content: Content extracted from the URL

        Returns:
            Generated summary
        """
        try:
            # Create prompt
            prompt = self._create_prompt(story, content)

            # Configure model
            generation_config = {
                "max_output_tokens": self.max_tokens,
                "temperature": 0.4,
                "top_p": 0.95,
            }

            logger.info(f"Using Gemini model: {self.model}")

            # Generate response
            try:
                model = self.genai.GenerativeModel(model_name=self.model, generation_config=generation_config)

                response = model.generate_content(prompt)

                # Extract summary from response
                summary = response.text.strip()

                return summary
            except ImportError as e:
                logger.error(f"ImportError with google.generativeai: {str(e)}")
                raise
            except AttributeError as e:
                logger.error(f"AttributeError with Gemini API: {str(e)}")
                raise
            except ValueError as e:
                logger.error(f"ValueError with Gemini API (possibly invalid model name '{self.model}'): {str(e)}")
                raise

        except Exception as e:
            logger.error(f"Gemini API request failed: {str(e)}")
            raise

    def _create_prompt(self, story: Dict[str, Any], content: Dict[str, Any]) -> str:
        """Create a prompt for the Gemini API."""
        return f"""
Please summarize the following article from Hacker News in Japanese:

Title: {story.get('title', 'Unknown Title')}
URL: {story.get('url', 'No URL')}
Points: {story.get('score', 0)}
Comments: {story.get('descendants', 0)}

Content:
{content.get('content', 'No content available')[:4000]}

記事の主要なポイント、重要な洞察、重要な詳細を捉えた簡潔な要約（3〜5段落）を日本語で提供してください。
要約は元の記事を読んでいない人にとって有益で分かりやすいものにしてください。
前置きは含めず、直接要約の内容から始めてください。
箇条書きではなく、流れのある文章形式で提供してください。
"""


class Summarizer:
    """
    Service for summarizing content using various LLM providers.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Summarizer service.

        Args:
            config: Configuration dictionary for the summarizer
        """
        self.config = config
        self.provider = self._initialize_provider()

    def _initialize_provider(self) -> LLMProvider:
        """Initialize the LLM provider based on configuration."""
        provider_name = self.config.get("provider", "openai").lower()

        if provider_name == "gemini":
            api_key = self.config.get("gemini_api_key")
            logger.info(f"Gemini API key present: {bool(api_key)}")
            logger.info(f"Gemini config: {self.config}")

            if not api_key:
                raise ValueError("Google API key is required for Gemini")

            model = self.config.get("gemini_model", "gemini-1.5-flash-latest")
            max_tokens = self.config.get("max_tokens", 500)

            return GeminiProvider(api_key, model, max_tokens)

        else:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")

    def summarize(self, story: Dict[str, Any], content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize the content of a story.

        Args:
            story: Story metadata from Hacker News
            content: Content extracted from the URL

        Returns:
            Dictionary containing the story, content, and summary
        """
        try:
            logger.info(f"Summarizing story: {story.get('title', 'Unknown')}")

            # Generate summary using the provider
            summary_text = self.provider.generate_summary(story, content)

            # Create result dictionary
            result = {
                "story": story,
                "content": {
                    "title": content.get("title"),
                    "url": content.get("url"),
                    "domain": content.get("domain"),
                    "content_length": len(content.get("content", "")),
                },
                "summary": summary_text,
                "summarized_at": time.time(),
            }

            logger.info(f"Successfully summarized story: {story.get('title', 'Unknown')}")
            return result

        except Exception as e:
            logger.error(f"Error summarizing story: {str(e)}")
            raise
