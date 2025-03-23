#!/usr/bin/env python3
"""
Very simple test script to verify the fix for SlackDelivery.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from services.delivery import SlackDelivery

# Create a mock SlackDelivery instance
slack_delivery = SlackDelivery({"webhook_url": "https://hooks.slack.com/services/xxx/yyy/zzz"})

# Test case: Summary without url at the top level
summary = {"summary": "This is a test summary."}

# This would have caused a KeyError: 'url' before our fix
try:
    blocks = slack_delivery._create_message_blocks([summary])
    with open("test_result_slack.txt", "w") as f:
        f.write("Test passed! No KeyError was raised.\n")
        f.write(str(blocks))
except KeyError as e:
    with open("test_result_slack.txt", "w") as f:
        f.write(f"Test failed! KeyError was raised: {e}\n")
except Exception as e:
    with open("test_result_slack.txt", "w") as f:
        f.write(f"Test failed! Exception was raised: {e}\n")
