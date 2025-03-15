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
    elif config['summarizer']['provider'] == 'openai':
        env_key = os.environ.get('OPENAI_API_KEY')
        if env_key and not config['summarizer'].get('openai_api_key'):
            config['summarizer']['openai_api_key'] = env_key
    elif config['summarizer']['provider'] == 'anthropic':
        env_key = os.environ.get('ANTHROPIC_API_KEY')
        if env_key and not config['summarizer'].get('anthropic_api_key'):
            config['summarizer']['anthropic_api_key'] = env_key
    
    # Delivery credentials
    if config['delivery']['method'] == 'email':
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
        
        config['delivery']['email'] = email_config
    
    elif config['delivery']['method'] == 'slack':
        slack_config = config['delivery'].get('slack', {})
        if not slack_config.get('webhook_url'):
            slack_config['webhook_url'] = os.environ.get('SLACK_WEBHOOK_URL')
        config['delivery']['slack'] = slack_config
    
    elif config['delivery']['method'] == 'line':
        line_config = config['delivery'].get('line', {})
        if not line_config.get('access_token'):
            line_config['access_token'] = os.environ.get('LINE_ACCESS_TOKEN')
        config['delivery']['line'] = line_config
