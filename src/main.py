#!/usr/bin/env python3
"""
HN Summarizer - A tool to fetch, summarize, and deliver top Hacker News stories.
"""
import logging
import argparse
from datetime import datetime

from utils.logger import setup_logger
from services.hn_fetcher import HNFetcher
from services.content_extractor import ContentExtractor
from services.summarizer import Summarizer
from services.delivery import DeliveryService
from config.settings import load_config

logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Fetch and summarize top Hacker News stories')
    parser.add_argument('--config', type=str, default='config.yaml', 
                        help='Path to configuration file')
    parser.add_argument('--top', type=int, default=10, 
                        help='Number of top stories to fetch (default: 10)')
    parser.add_argument('--delivery', type=str, choices=['email', 'slack', 'line'], 
                        help='Delivery method override')
    parser.add_argument('--debug', action='store_true', 
                        help='Enable debug logging')
    return parser.parse_args()

def main():
    """Main function to run the HN summarizer."""
    args = parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logger(log_level)
    
    logger.info(f"Starting HN Summarizer at {datetime.now().isoformat()}")
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Override config with command line args if provided
        if args.delivery:
            config['delivery']['method'] = args.delivery
        
        # Initialize services
        hn_fetcher = HNFetcher()
        content_extractor = ContentExtractor()
        summarizer = Summarizer(config['summarizer'])
        delivery_service = DeliveryService(config['delivery'])
        
        # Fetch top stories
        logger.info(f"Fetching top {args.top} stories from Hacker News")
        top_stories = hn_fetcher.fetch_top_stories(args.top)
        
        # Process each story
        summaries = []
        for story in top_stories:
            try:
                # Extract content
                logger.info(f"Extracting content from: {story['url']}")
                content = content_extractor.extract(story['url'])
                
                # Summarize content
                logger.info(f"Summarizing: {story['title']}")
                summary = summarizer.summarize(story, content)
                
                summaries.append(summary)
            except Exception as e:
                logger.error(f"Error processing story {story['title']}: {str(e)}")
        
        # Deliver summaries
        if summaries:
            logger.info(f"Delivering {len(summaries)} summaries via {config['delivery']['method']}")
            delivery_service.deliver(summaries)
            logger.info("Delivery completed successfully")
        else:
            logger.warning("No summaries to deliver")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise
    
    logger.info(f"HN Summarizer completed at {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()
