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
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash-latest", max_tokens: int = 500):
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
                model = self.genai.GenerativeModel(
                    model_name=self.model,
                    generation_config=generation_config
                )
                
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
"""

class OpenAIProvider(LLMProvider):
    """OpenAI API provider for summarization."""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", max_tokens: int = 500):
        """
        Initialize the OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-3.5-turbo)
            max_tokens: Maximum tokens for the summary
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    def generate_summary(self, story: Dict[str, Any], content: Dict[str, Any]) -> str:
        """
        Generate a summary using OpenAI.
        
        Args:
            story: Story metadata from Hacker News
            content: Content extracted from the URL
            
        Returns:
            Generated summary
        """
        try:
            # Create prompt
            prompt = self._create_prompt(story, content)
            
            # Prepare request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that summarizes articles."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": self.max_tokens,
                "temperature": 0.5
            }
            
            # Make API request
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            # Extract summary from response
            result = response.json()
            summary = result["choices"][0]["message"]["content"].strip()
            
            return summary
            
        except requests.RequestException as e:
            logger.error(f"OpenAI API request failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error generating summary with OpenAI: {str(e)}")
            raise
    
    def _create_prompt(self, story: Dict[str, Any], content: Dict[str, Any]) -> str:
        """Create a prompt for the OpenAI API."""
        return f"""
Please summarize the following article from Hacker News:

Title: {story.get('title', 'Unknown Title')}
URL: {story.get('url', 'No URL')}
Points: {story.get('score', 0)}
Comments: {story.get('descendants', 0)}

Content:
{content.get('content', 'No content available')[:4000]}

Provide a concise summary (3-5 paragraphs) that captures the main points, key insights, and any important details. 
The summary should be informative and helpful for someone who hasn't read the original article.
"""

class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider for summarization."""
    
    def __init__(self, api_key: str, model: str = "claude-instant-1", max_tokens: int = 500):
        """
        Initialize the Anthropic provider.
        
        Args:
            api_key: Anthropic API key
            model: Model to use (default: claude-instant-1)
            max_tokens: Maximum tokens for the summary
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.api_url = "https://api.anthropic.com/v1/messages"
    
    def generate_summary(self, story: Dict[str, Any], content: Dict[str, Any]) -> str:
        """
        Generate a summary using Anthropic Claude.
        
        Args:
            story: Story metadata from Hacker News
            content: Content extracted from the URL
            
        Returns:
            Generated summary
        """
        try:
            # Create prompt
            prompt = self._create_prompt(story, content)
            
            # Prepare request
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": self.max_tokens
            }
            
            # Make API request
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            # Extract summary from response
            result = response.json()
            summary = result["content"][0]["text"].strip()
            
            return summary
            
        except requests.RequestException as e:
            logger.error(f"Anthropic API request failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error generating summary with Anthropic: {str(e)}")
            raise
    
    def _create_prompt(self, story: Dict[str, Any], content: Dict[str, Any]) -> str:
        """Create a prompt for the Anthropic API."""
        return f"""
Please summarize the following article from Hacker News:

Title: {story.get('title', 'Unknown Title')}
URL: {story.get('url', 'No URL')}
Points: {story.get('score', 0)}
Comments: {story.get('descendants', 0)}

Content:
{content.get('content', 'No content available')[:4000]}

Provide a concise summary (3-5 paragraphs) that captures the main points, key insights, and any important details. 
The summary should be informative and helpful for someone who hasn't read the original article.
"""

class OllamaProvider(LLMProvider):
    """Ollama local LLM provider for summarization."""
    
    def __init__(self, model: str = "llama2", host: str = "http://localhost:11434", max_tokens: int = 500):
        """
        Initialize the Ollama provider.
        
        Args:
            model: Model to use (default: llama2)
            host: Ollama host URL
            max_tokens: Maximum tokens for the summary
        """
        self.model = model
        self.host = host
        self.max_tokens = max_tokens
        self.api_url = f"{host}/api/generate"
    
    def generate_summary(self, story: Dict[str, Any], content: Dict[str, Any]) -> str:
        """
        Generate a summary using Ollama local LLM.
        
        Args:
            story: Story metadata from Hacker News
            content: Content extracted from the URL
            
        Returns:
            Generated summary
        """
        try:
            # Create prompt
            prompt = self._create_prompt(story, content)
            
            # Prepare request
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": self.max_tokens,
                    "temperature": 0.5
                }
            }
            
            # Make API request
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=120  # Local LLMs might be slower
            )
            response.raise_for_status()
            
            # Extract summary from response
            result = response.json()
            summary = result.get("response", "").strip()
            
            return summary
            
        except requests.RequestException as e:
            logger.error(f"Ollama API request failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error generating summary with Ollama: {str(e)}")
            raise
    
    def _create_prompt(self, story: Dict[str, Any], content: Dict[str, Any]) -> str:
        """Create a prompt for the Ollama API."""
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
        provider_name = self.config.get('provider', 'openai').lower()
        
        if provider_name == 'openai':
            api_key = self.config.get('openai_api_key')
            if not api_key:
                raise ValueError("OpenAI API key is required")
            
            model = self.config.get('openai_model', 'gpt-3.5-turbo')
            max_tokens = self.config.get('max_tokens', 500)
            
            return OpenAIProvider(api_key, model, max_tokens)
            
        elif provider_name == 'gemini':
            api_key = self.config.get('gemini_api_key')
            logger.info(f"Gemini API key present: {bool(api_key)}")
            logger.info(f"Gemini config: {self.config}")
            
            if not api_key:
                raise ValueError("Google API key is required for Gemini")
            
            model = self.config.get('gemini_model', 'gemini-1.5-flash-latest')
            max_tokens = self.config.get('max_tokens', 500)
            
            return GeminiProvider(api_key, model, max_tokens)
            
        elif provider_name == 'anthropic':
            api_key = self.config.get('anthropic_api_key')
            if not api_key:
                raise ValueError("Anthropic API key is required")
            
            model = self.config.get('anthropic_model', 'claude-instant-1')
            max_tokens = self.config.get('max_tokens', 500)
            
            return AnthropicProvider(api_key, model, max_tokens)
            
        elif provider_name == 'ollama':
            model = self.config.get('ollama_model', 'llama2')
            host = self.config.get('ollama_host', 'http://localhost:11434')
            max_tokens = self.config.get('max_tokens', 500)
            
            return OllamaProvider(model, host, max_tokens)
            
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
                'story': story,
                'content': {
                    'title': content.get('title'),
                    'url': content.get('url'),
                    'domain': content.get('domain'),
                    'content_length': len(content.get('content', '')),
                },
                'summary': summary_text,
                'summarized_at': time.time()
            }
            
            logger.info(f"Successfully summarized story: {story.get('title', 'Unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Error summarizing story: {str(e)}")
            raise
