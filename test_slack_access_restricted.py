#!/usr/bin/env python3
"""
Test script to verify handling of access-restricted stories in Slack delivery.
"""
import sys
import os
import time
import json

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from services.delivery import SlackDelivery

def main():
    """Test handling of access-restricted stories in Slack delivery."""
    # Create a mock SlackDelivery instance
    slack_delivery = SlackDelivery({
        'webhook_url': 'https://hooks.slack.com/services/xxx/yyy/zzz'
    })
    
    # Create a mock story with access restrictions
    restricted_story = {
        'story': {
            'title': 'Access Restricted Story',
            'url': 'https://example.com/restricted',
            'score': 100,
            'descendants': 50,
            'by': 'testuser',
            'id': '12345'
        },
        'content': {
            'url': 'https://example.com/restricted',
            'domain': 'example.com',
            'title': 'Access Restricted Story',
            'content_length': 0,
        },
        'summary': "このコンテンツはアクセス制限があるため要約できませんでした。",
        'access_restricted': True,
        'summarized_at': time.time()
    }
    
    # Create a mock regular story
    regular_story = {
        'story': {
            'title': 'Regular Story',
            'url': 'https://example.com/regular',
            'score': 100,
            'descendants': 50,
            'by': 'testuser',
            'id': '67890'
        },
        'content': {
            'url': 'https://example.com/regular',
            'domain': 'example.com',
            'title': 'Regular Story',
            'content_length': 1000,
        },
        'summary': "This is a regular story summary.",
        'summarized_at': time.time()
    }
    
    # Test creating message blocks with both stories
    blocks = slack_delivery._create_message_blocks([restricted_story, regular_story])
    
    # Print the blocks as JSON for inspection
    print(json.dumps(blocks, indent=2))
    
    # Write the blocks to a file for inspection
    with open('test_slack_blocks.json', 'w') as f:
        json.dump(blocks, f, indent=2)
    print("\nSlack blocks written to test_slack_blocks.json")

if __name__ == "__main__":
    main()
