#!/usr/bin/env python3
"""
Very simple test script to verify the fix.
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from services.delivery import EmailDelivery

# Create a mock EmailDelivery instance
email_delivery = EmailDelivery({
    'username': 'test@example.com',
    'password': 'password',
    'recipients': ['recipient@example.com']
})

# Test case: Summary without url at the top level
summary = {
    'summary': 'This is a test summary.'
}

# This would have caused a KeyError: 'url' before our fix
try:
    result = email_delivery._format_summary_for_email(summary, index=1)
    with open('test_result.txt', 'w') as f:
        f.write("Test passed! No KeyError was raised.\n")
        f.write(result)
except KeyError as e:
    with open('test_result.txt', 'w') as f:
        f.write(f"Test failed! KeyError was raised: {e}\n")
except Exception as e:
    with open('test_result.txt', 'w') as f:
        f.write(f"Test failed! Exception was raised: {e}\n")
