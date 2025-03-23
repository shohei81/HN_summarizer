"""
Service for fetching stories from Hacker News API.
"""

import logging
import requests
from typing import List, Dict, Any
import time

logger = logging.getLogger(__name__)


class HNFetcher:
    """
    Service for fetching stories from the Hacker News API.

    The Hacker News API is a simple, RESTful API that provides access to Hacker News stories,
    comments, and user data.

    API Documentation: https://github.com/HackerNews/API
    """

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self, request_delay: float = 0.5):
        """
        Initialize the HN Fetcher.

        Args:
            request_delay: Delay between API requests in seconds to avoid rate limiting
        """
        self.request_delay = request_delay

    def fetch_top_stories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch the top stories from Hacker News.

        Args:
            limit: Number of top stories to fetch (default: 10)

        Returns:
            List of story objects with details
        """
        try:
            # Get IDs of top stories
            top_stories_url = f"{self.BASE_URL}/topstories.json"
            response = requests.get(top_stories_url, timeout=10)
            response.raise_for_status()

            story_ids = response.json()[:limit]
            logger.debug(f"Fetched {len(story_ids)} top story IDs")

            # Fetch details for each story
            stories = []
            for story_id in story_ids:
                story = self._fetch_story(story_id)
                if story and "url" in story:  # Only include stories with URLs
                    stories.append(story)
                time.sleep(self.request_delay)  # Avoid rate limiting

            logger.info(f"Successfully fetched {len(stories)} stories with URLs")
            return stories

        except requests.RequestException as e:
            logger.error(f"Error fetching top stories: {str(e)}")
            raise

    def _fetch_story(self, story_id: int) -> Dict[str, Any]:
        """
        Fetch details for a specific story.

        Args:
            story_id: The ID of the story to fetch

        Returns:
            Story details as a dictionary
        """
        try:
            story_url = f"{self.BASE_URL}/item/{story_id}.json"
            response = requests.get(story_url, timeout=10)
            response.raise_for_status()

            story = response.json()
            logger.debug(f"Fetched story: {story.get('title', 'Unknown')}")

            # Add a timestamp for when we fetched this story
            story["fetched_at"] = time.time()

            return story

        except requests.RequestException as e:
            logger.error(f"Error fetching story {story_id}: {str(e)}")
            return None
