#!/usr/bin/env python3
"""
Test script to verify HN Summarizer functionality.
This script fetches a single story from Hacker News and tests the summarization.
It doesn't send any notifications, just prints the summary to the console.
"""

import logging
import sys
import os
import json
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from utils.logger import setup_logger
from services.hn_fetcher import HNFetcher
from services.content_extractor import ContentExtractor
from services.summarizer import Summarizer
from config.settings import load_config


def main():
    """Run a test of the HN Summarizer."""
    # Setup logging
    setup_logger(logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("Starting HN Summarizer test run")

    try:
        # Load configuration
        config_path = "config.yaml"
        if not os.path.exists(config_path):
            logger.warning(f"Configuration file {config_path} not found, using example config")
            config_path = "config.yaml.example"

        config = load_config(config_path)

        # Check for API keys
        if config["summarizer"]["provider"] == "gemini" and not config["summarizer"].get("gemini_api_key"):
            logger.warning("Gemini API key not found in config or environment variables")
            logger.info("This test will fetch content but won't be able to summarize without an API key")
        elif config["summarizer"]["provider"] == "openai" and not config["summarizer"].get("openai_api_key"):
            logger.warning("OpenAI API key not found in config or environment variables")
            logger.info("This test will fetch content but won't be able to summarize without an API key")

        # Initialize services
        hn_fetcher = HNFetcher()
        content_extractor = ContentExtractor()

        # Fetch a single top story
        logger.info("Fetching top story from Hacker News")
        top_stories = hn_fetcher.fetch_top_stories(1)

        if not top_stories:
            logger.error("No stories fetched from Hacker News")
            return

        story = top_stories[0]
        logger.info(f"Fetched story: {story['title']}")
        logger.info(f"URL: {story['url']}")

        # Extract content
        logger.info(f"Extracting content from: {story['url']}")
        content = content_extractor.extract(story["url"])

        logger.info(f"Successfully extracted {len(content['content'])} characters")

        # Try to summarize if API key is available
        try:
            summarizer = Summarizer(config["summarizer"])
            logger.info(f"Summarizing with {config['summarizer']['provider']}")
            summary = summarizer.summarize(story, content)

            # Print the summary
            print("\n" + "=" * 80)
            print(f"TITLE: {story['title']}")
            print(f"URL: {story['url']}")
            print(f"POINTS: {story['score']} | COMMENTS: {story['descendants']}")
            print("-" * 80)
            print(summary["summary"])
            print("=" * 80 + "\n")

            logger.info("Summary generated successfully")
        except Exception as e:
            logger.error(f"Error summarizing content: {str(e)}")
            logger.info("Content extraction was successful, but summarization failed")
            logger.info("Check your API keys and configuration")

        logger.info("Test completed successfully")

    except Exception as e:
        logger.error(f"An error occurred during the test: {str(e)}")
        raise


if __name__ == "__main__":
    main()
