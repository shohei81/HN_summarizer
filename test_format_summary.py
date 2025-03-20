#!/usr/bin/env python3
"""
Simple test script to verify the _format_summary_for_email method.
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from services.delivery import EmailDelivery

def main():
    """Test the _format_summary_for_email method."""
    # Create a mock EmailDelivery instance
    email_delivery = EmailDelivery({
        'username': 'test@example.com',
        'password': 'password',
        'recipients': ['recipient@example.com']
    })
    
    # Test case 1: Summary with story containing url and title
    summary1 = {
        'story': {
            'title': 'Test Story',
            'url': 'https://example.com/test',
            'by': 'testuser',
            'id': '12345'
        },
        'summary': 'This is a test summary.'
    }
    
    # Test case 2: Summary without story
    summary2 = {
        'summary': 'This is a test summary without story.'
    }
    
    # Test case 3: Summary with empty story
    summary3 = {
        'story': {},
        'summary': 'This is a test summary with empty story.'
    }
    
    # Test case 4: Summary with access_restricted
    summary4 = {
        'story': {
            'title': 'Restricted Story',
            'url': 'https://example.com/restricted',
            'by': 'testuser',
            'id': '12345'
        },
        'access_restricted': True,
        'summary': 'This summary should not be shown.'
    }
    
    # Test the method with each test case
    print("Test Case 1: Summary with story containing url and title")
    result1 = email_delivery._format_summary_for_email(summary1, index=1)
    print(result1)
    print("\n" + "-" * 80 + "\n")
    
    print("Test Case 2: Summary without story")
    result2 = email_delivery._format_summary_for_email(summary2, index=2)
    print(result2)
    print("\n" + "-" * 80 + "\n")
    
    print("Test Case 3: Summary with empty story")
    result3 = email_delivery._format_summary_for_email(summary3, index=3)
    print(result3)
    print("\n" + "-" * 80 + "\n")
    
    print("Test Case 4: Summary with access_restricted")
    result4 = email_delivery._format_summary_for_email(summary4, index=4)
    print(result4)

if __name__ == "__main__":
    main()
