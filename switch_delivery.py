#!/usr/bin/env python3
"""
Utility script to switch between delivery methods in the config.yaml file.
"""
import argparse
import logging
import os
import sys
import yaml

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Switch delivery method in config.yaml')
    parser.add_argument('method', type=str, choices=['email', 'slack', 'email,slack', 'slack,email'],
                        help='Delivery method to switch to (can be comma-separated for multiple methods)')
    parser.add_argument('--config', type=str, default='config.yaml',
                        help='Path to configuration file (default: config.yaml)')
    return parser.parse_args()

def switch_delivery_method(config_path, method):
    """
    Switch the delivery method in the config.yaml file.
    
    Args:
        config_path: Path to the configuration file
        method: Delivery method to switch to ('email', 'slack', or 'line')
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if config file exists
        if not os.path.exists(config_path):
            logger.error(f"Configuration file {config_path} not found")
            return False
        
        # Read the config file
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check if the config has the expected structure
        if 'delivery' not in config:
            logger.error("Invalid config file: 'delivery' section not found")
            return False
        
        # Update the delivery method
        current_method = config['delivery'].get('method', 'unknown')
        if current_method == method:
            logger.info(f"Delivery method is already set to '{method}'")
            return True
        
        config['delivery']['method'] = method
        
        # Write the updated config back to the file
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Successfully switched delivery method from '{current_method}' to '{method}'")
        return True
        
    except Exception as e:
        logger.error(f"Error switching delivery method: {str(e)}")
        return False

def main():
    """Main function."""
    args = parse_args()
    
    # Switch delivery method
    success = switch_delivery_method(args.config, args.method)
    
    if not success:
        logger.error("Failed to switch delivery method")
        sys.exit(1)
    
    logger.info(f"Delivery method switched to '{args.method}'")
    
    # Provide next steps based on the selected method(s)
    methods = args.method.split(',')
    
    logger.info("Next steps:")
    
    if 'email' in methods:
        logger.info("For Email delivery:")
        logger.info("- Ensure EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_SENDER, and EMAIL_RECIPIENTS environment variables are set")
    
    if 'slack' in methods:
        logger.info("For Slack delivery:")
        logger.info("- Ensure SLACK_WEBHOOK_URL environment variable is set")
        logger.info("- You can test the Slack webhook with: ./slack_webhook_test.py")
    
    logger.info("Run the application with: python src/main.py")

if __name__ == "__main__":
    main()
