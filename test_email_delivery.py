#!/usr/bin/env python3
"""
Test script to verify the email delivery functionality.
This script creates a mock summary and tests the email delivery.
"""
import logging
import sys
import os
import time
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from utils.logger import setup_logger
from services.delivery import EmailDelivery
from config.settings import load_config

def main():
    """Run a test of the email delivery."""
    # Setup logging
    setup_logger(logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Also log to console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)
    
    print("Starting email delivery test")
    logger.info("Starting email delivery test")
    
    try:
        # Load configuration
        config_path = 'config.yaml'
        if not os.path.exists(config_path):
            logger.warning(f"Configuration file {config_path} not found, using example config")
            config_path = 'config.yaml.example'
        
        config = load_config(config_path)
        
        # Create a mock summary
        mock_summary = {
            'story': {
                'title': 'Test Story',
                'url': 'https://example.com/test',
                'score': 100,
                'descendants': 50,
                'by': 'testuser',
                'id': '12345'
            },
            'content': {
                'title': 'Test Story',
                'url': 'https://example.com/test',
                'domain': 'example.com',
                'content_length': 1000
            },
            'summary': 'This is a test summary for the email delivery test.',
            'summarized_at': time.time()
        }
        
        # Initialize email delivery
        email_config = config.get('delivery', {}).get('email', {})
        if not email_config:
            logger.error("Email configuration not found in config")
            return
        
        email_delivery = EmailDelivery(email_config)
        
        # Test email delivery
        logger.info("Testing email delivery")
        success = email_delivery.send([mock_summary])
        
        if success:
            logger.info("Email delivery test completed successfully")
        else:
            logger.error("Email delivery test failed")
        
    except Exception as e:
        logger.error(f"An error occurred during the test: {str(e)}")
        raise

if __name__ == "__main__":
    main()
