#!/usr/bin/env python3
"""
Test script for Slack webhook integration.
This script sends a test message to Slack using the webhook URL.
"""

import argparse
import json
import logging
import os
import sys
import requests
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test Slack webhook integration")
    parser.add_argument(
        "--webhook-url",
        type=str,
        help="Slack webhook URL (or set SLACK_WEBHOOK_URL environment variable)",
    )
    parser.add_argument(
        "--channel",
        type=str,
        help="Slack channel to post to (optional, overrides webhook default)",
    )
    return parser.parse_args()


def send_test_message(webhook_url, channel=None):
    """
    Send a test message to Slack using the webhook URL.

    Args:
        webhook_url: Slack webhook URL
        channel: Optional channel to post to (overrides webhook default)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create message blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "HN Summarizer - Test Message",
                    "emoji": True,
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*This is a test message from HN Summarizer*\n\nIf you're seeing this, your Slack webhook integration is working correctly! 🎉",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    }
                ],
            },
        ]

        # Prepare payload
        payload = {
            "username": "HN Summarizer Bot",
            "icon_emoji": ":newspaper:",
            "blocks": blocks,
        }

        # Add channel if provided
        if channel:
            payload["channel"] = channel

        # Send to Slack
        logger.info(f"Sending test message to Slack...")
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        response.raise_for_status()

        logger.info(f"Test message sent successfully! Response: {response.status_code}")
        return True

    except requests.RequestException as e:
        logger.error(f"Error sending to Slack: {str(e)}")
        if hasattr(e, "response") and e.response:
            logger.error(f"Response: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"Error in Slack delivery: {str(e)}")
        return False


def main():
    """Main function."""
    args = parse_args()

    # Get webhook URL from args or environment variable
    webhook_url = args.webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.error(
            "Slack webhook URL is required. Provide it as an argument or set the SLACK_WEBHOOK_URL environment variable."
        )
        sys.exit(1)

    # Get channel from args or environment variable
    channel = args.channel or os.environ.get("SLACK_CHANNEL")

    # Send test message
    success = send_test_message(webhook_url, channel)

    if not success:
        logger.error("Failed to send test message to Slack.")
        sys.exit(1)

    logger.info("Test completed successfully!")


if __name__ == "__main__":
    main()
