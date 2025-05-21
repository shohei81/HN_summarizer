#!/usr/bin/env python3
"""
Test script to verify handling of access-restricted stories.
"""

import sys
import os
import time

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from services.delivery import EmailDelivery


def main():
    """Test handling of access-restricted stories."""
    # Create a mock EmailDelivery instance
    email_delivery = EmailDelivery(
        {
            "username": "test@example.com",
            "password": "password",
            "recipients": ["recipient@example.com"],
        }
    )

    # Create a mock story with access restrictions
    restricted_story = {
        "story": {
            "title": "Access Restricted Story",
            "url": "https://example.com/restricted",
            "score": 100,
            "descendants": 50,
            "by": "testuser",
            "id": "12345",
        },
        "content": {
            "url": "https://example.com/restricted",
            "domain": "example.com",
            "title": "Access Restricted Story",
            "content_length": 0,
        },
        "summary": "このコンテンツはアクセス制限があるため要約できませんでした。",
        "access_restricted": True,
        "summarized_at": time.time(),
    }

    # Create a mock regular story
    regular_story = {
        "story": {
            "title": "Regular Story",
            "url": "https://example.com/regular",
            "score": 100,
            "descendants": 50,
            "by": "testuser",
            "id": "67890",
        },
        "content": {
            "url": "https://example.com/regular",
            "domain": "example.com",
            "title": "Regular Story",
            "content_length": 1000,
        },
        "summary": "This is a regular story summary.",
        "summarized_at": time.time(),
    }

    # Test formatting both stories
    print("=== Access Restricted Story ===")
    restricted_html = email_delivery._format_summary_for_email(restricted_story, index=1)
    print(restricted_html)

    print("\n=== Regular Story ===")
    regular_html = email_delivery._format_summary_for_email(regular_story, index=2)
    print(regular_html)

    # Test creating HTML content with both stories
    print("\n=== Complete HTML Email ===")
    html_content = email_delivery._create_html_content([restricted_story, regular_story])
    print(html_content)

    # Write the HTML content to a file for inspection
    with open(os.path.join("output", "test_email.html"), "w") as f:
        f.write(html_content)
    print("\nHTML content written to test_email.html")


if __name__ == "__main__":
    main()
