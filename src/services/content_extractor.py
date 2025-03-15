"""
Service for extracting content from web pages.
"""
import logging
import requests
from bs4 import BeautifulSoup
import time
from typing import Optional
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class ContentExtractor:
    """
    Service for extracting content from web pages.
    
    This service fetches web pages and extracts the main content,
    attempting to filter out navigation, ads, and other non-content elements.
    """
    
    def __init__(self, timeout: int = 30, user_agent: Optional[str] = None):
        """
        Initialize the Content Extractor.
        
        Args:
            timeout: Request timeout in seconds
            user_agent: Custom User-Agent string to use for requests
        """
        self.timeout = timeout
        self.user_agent = user_agent or 'HN Summarizer Bot/1.0'
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
    
    def extract(self, url: str) -> dict:
        """
        Extract content from a URL.
        
        Args:
            url: The URL to extract content from
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        try:
            logger.debug(f"Fetching content from: {url}")
            
            # Fetch the page
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract basic metadata
            title = self._extract_title(soup)
            domain = urlparse(url).netloc
            
            # Extract the main content
            content = self._extract_main_content(soup)
            
            # Create result dictionary
            result = {
                'url': url,
                'domain': domain,
                'title': title,
                'content': content,
                'html': response.text,  # Store the full HTML for potential further processing
                'extracted_at': time.time()
            }
            
            content_length = len(content)
            logger.info(f"Successfully extracted {content_length} characters from {url}")
            
            return result
            
        except requests.RequestException as e:
            logger.error(f"Error fetching URL {url}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {str(e)}")
            raise
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the title from the page."""
        if soup.title:
            return soup.title.string.strip()
        return "No title found"
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extract the main content from the page.
        
        This uses a simple heuristic approach to find the main content:
        1. Look for common content containers
        2. Fall back to the body if no specific container is found
        3. Clean up the content by removing scripts, styles, etc.
        """
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Try to find main content container
        main_content = None
        
        # Look for common content containers by ID
        for id_value in ['content', 'main', 'article', 'post', 'entry']:
            element = soup.find(id=re.compile(f"^{id_value}$|^main-{id_value}$", re.I))
            if element:
                main_content = element
                break
        
        # Look for common content containers by class
        if not main_content:
            for class_value in ['content', 'article', 'post', 'entry', 'story']:
                element = soup.find(class_=re.compile(f"^{class_value}$|^main-{class_value}$", re.I))
                if element:
                    main_content = element
                    break
        
        # Look for article tag
        if not main_content:
            main_content = soup.find('article')
        
        # Fall back to body if no specific container is found
        if not main_content:
            main_content = soup.body
        
        # If still nothing found, use the whole soup
        if not main_content:
            main_content = soup
        
        # Get text and clean it up
        text = main_content.get_text(separator=' ', strip=True)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
