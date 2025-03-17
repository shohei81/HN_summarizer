"""
Configuration settings for the HN Summarizer.
"""
import logging
import os
import yaml
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        logger.info(f"Loading configuration from {config_path}")
        
        if not os.path.exists(config_path):
            logger.warning(f"Configuration file {config_path} not found, using default configuration")
            return get_default_config()
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate and merge with defaults
        validated_config = validate_config(config)
        
        logger.info(f"Configuration loaded successfully")
        return validated_config
        
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        logger.warning("Falling back to default configuration")
        return get_default_config()

def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration.
    
    Returns:
        Default configuration dictionary
    """
    return {
        'summarizer': {
            'provider': 'gemini',
            'gemini_model': 'gemini-1.5-flash-latest',
            'max_tokens': 500,
            # API keys should be provided via environment variables or config file
        },
        'delivery': {
            'method': 'email',
            'email': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                # Credentials should be provided via environment variables or config file
            },
            'slack': {
                'username': 'HN Summarizer Bot',
                'icon_emoji': ':newspaper:',
                'max_summaries_per_message': 3,
                # webhook_url should be provided via environment variables or config file
            }
        },
        'security': {
            'use_environment_variables': True,
            'encrypt_api_keys': False,
        }
    }

def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize configuration.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Validated configuration dictionary
    """
    default_config = get_default_config()
    
    # Ensure top-level sections exist
    for section in default_config:
        if section not in config:
            config[section] = {}
    
    # Validate summarizer section
    if 'provider' not in config['summarizer']:
        config['summarizer']['provider'] = default_config['summarizer']['provider']
    
    # Check for environment variables if configured
    if config.get('security', {}).get('use_environment_variables', True):
        _load_from_environment(config)
    
    return config

def _load_from_environment(config: Dict[str, Any]) -> None:
    """
    Load sensitive configuration from environment variables.
    
    Args:
        config: Configuration dictionary to update
    """
    # LLM API keys
    if config['summarizer']['provider'] == 'gemini':
        # Only override if the environment variable exists and the config doesn't already have a key
        env_key = os.environ.get('GEMINI_API_KEY')
        if env_key and not config['summarizer'].get('gemini_api_key'):
            config['summarizer']['gemini_api_key'] = env_key
    
    # Delivery credentials
    # Get delivery methods (support for comma-separated list)
    delivery_methods = config['delivery']['method'].split(',')
    
    # Email configuration
    if 'email' in delivery_methods:
        email_config = config['delivery'].get('email', {})
        # Only use environment variables if the config doesn't already have values
        if not email_config.get('username'):
            email_config['username'] = os.environ.get('EMAIL_USERNAME')
        if not email_config.get('password'):
            email_config['password'] = os.environ.get('EMAIL_PASSWORD')
        
        # Get recipients from environment variable if available
        recipients_env = os.environ.get('EMAIL_RECIPIENTS')
        if recipients_env:
            try:
                # Parse comma-separated list of email addresses
                recipients = [email.strip() for email in recipients_env.split(',')]
                email_config['recipients'] = recipients
            except Exception as e:
                logger.error(f"Error parsing EMAIL_RECIPIENTS: {str(e)}")
        
        # Get sender from environment variable if available
        sender_env = os.environ.get('EMAIL_SENDER')
        if sender_env and not email_config.get('sender'):
            email_config['sender'] = sender_env
        
        config['delivery']['email'] = email_config
    
    # Slack configuration
    if 'slack' in delivery_methods:
        slack_config = config['delivery'].get('slack', {})
        # Get webhook URL from environment variable if available
        webhook_url_env = os.environ.get('SLACK_WEBHOOK_URL')
        if webhook_url_env and not slack_config.get('webhook_url'):
            slack_config['webhook_url'] = webhook_url_env
        
        # Get channel from environment variable if available (optional)
        channel_env = os.environ.get('SLACK_CHANNEL')
        if channel_env and not slack_config.get('channel'):
            slack_config['channel'] = channel_env
        
        config['delivery']['slack'] = slack_config
