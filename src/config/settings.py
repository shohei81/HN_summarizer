"""
Configuration settings for the HN Summarizer.
"""

import logging
import os
import yaml
from typing import Dict, Any, Optional
from google.cloud import secretmanager
import google.auth

logger = logging.getLogger(__name__)


def _get_secret_from_gcp(secret_id: str) -> Optional[str]:
    """
    Retrieves a secret from Google Cloud Secret Manager.

    Args:
        secret_id: The ID of the secret in Secret Manager (e.g., "HN_SUMMARIZER_GEMINI_API_KEY").

    Returns:
        The secret value as a string, or None if an error occurs or the secret is not found.
    """
    try:
        # Attempt to get project_id from environment, then from default credentials
        project_id = os.environ.get("GCP_PROJECT_ID")
        if not project_id:
            _, project_id = google.auth.default()
        
        if not project_id:
            logger.warning("GCP_PROJECT_ID not set and could not be determined from credentials.")
            return None

        client = secretmanager.SecretManagerServiceClient()
        secret_name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(name=secret_name)
        payload = response.payload.data.decode("UTF-8")
        logger.info(f"Successfully fetched secret '{secret_id}' from GCP Secret Manager.")
        return payload
    except Exception as e:
        # Log softly, as we might not be in a GCP environment or the secret might not be mandatory
        logger.info(f"Could not fetch secret '{secret_id}' from GCP Secret Manager: {e}")
        return None


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

        with open(config_path, "r") as f:
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
        "summarizer": {
            "provider": "gemini",
            "gemini_model": "gemini-1.5-flash-latest",
            "max_tokens": 500,
            # API keys should be provided via environment variables or config file
        },
        "delivery": {
            "method": "email",
            "email": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                # Credentials should be provided via environment variables or config file
            },
            "slack": {
                "username": "HN Summarizer Bot",
                "icon_emoji": ":newspaper:",
                "max_summaries_per_message": 3,
                # webhook_url should be provided via environment variables or config file
            },
        },
        "security": {
            "use_environment_variables": True,
            "encrypt_api_keys": False,
            "use_gcp_secret_manager": True 
        },
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
    if "provider" not in config["summarizer"]:
        config["summarizer"]["provider"] = default_config["summarizer"]["provider"]

    # Check for environment variables if configured
    if config.get("security", {}).get("use_environment_variables", True):
        _load_from_environment(config)

    return config


def _load_from_environment(config: Dict[str, Any]) -> None:
    """
    Load sensitive configuration from environment variables, with a fallback to GCP Secret Manager.

    Args:
        config: Configuration dictionary to update
    """
    use_gcp = config.get("security", {}).get("use_gcp_secret_manager", True)

    # LLM API keys
    if config["summarizer"]["provider"] == "gemini":
        gemini_api_key_val = os.environ.get("GEMINI_API_KEY")
        if not gemini_api_key_val and use_gcp:
            gemini_api_key_val = _get_secret_from_gcp("HN_SUMMARIZER_GEMINI_API_KEY")
        
        if gemini_api_key_val and not config["summarizer"].get("gemini_api_key"):
            config["summarizer"]["gemini_api_key"] = gemini_api_key_val
            logger.info("Loaded Gemini API Key.")
        elif not config["summarizer"].get("gemini_api_key"):
            logger.warning("GEMINI_API_KEY not found in environment, GCP Secret Manager, or config file.")

    # Delivery credentials
    delivery_methods = config["delivery"]["method"].split(",")

    # Email configuration
    if "email" in delivery_methods:
        email_config = config["delivery"].get("email", {})
        
        email_username_val = os.environ.get("EMAIL_USERNAME")
        if not email_username_val and use_gcp:
            email_username_val = _get_secret_from_gcp("HN_SUMMARIZER_EMAIL_USERNAME")
        if email_username_val and not email_config.get("username"):
            email_config["username"] = email_username_val
            logger.info("Loaded EMAIL_USERNAME.")
        elif not email_config.get("username"):
            logger.warning("EMAIL_USERNAME not found in environment, GCP Secret Manager, or config file.")

        email_password_val = os.environ.get("EMAIL_PASSWORD")
        if not email_password_val and use_gcp:
            email_password_val = _get_secret_from_gcp("HN_SUMMARIZER_EMAIL_PASSWORD")
        if email_password_val and not email_config.get("password"):
            email_config["password"] = email_password_val
            logger.info("Loaded EMAIL_PASSWORD.")
        elif not email_config.get("password"):
            logger.warning("EMAIL_PASSWORD not found in environment, GCP Secret Manager, or config file.")

        email_sender_val = os.environ.get("EMAIL_SENDER")
        if not email_sender_val and use_gcp:
            email_sender_val = _get_secret_from_gcp("HN_SUMMARIZER_EMAIL_SENDER")
        if email_sender_val and not email_config.get("sender"):
            email_config["sender"] = email_sender_val
            logger.info("Loaded EMAIL_SENDER.")
        # No warning if sender is not found, as it might be optional or default to username

        email_recipients_val = os.environ.get("EMAIL_RECIPIENTS")
        if not email_recipients_val and use_gcp:
            email_recipients_val = _get_secret_from_gcp("HN_SUMMARIZER_EMAIL_RECIPIENTS")
        if email_recipients_val and not email_config.get("recipients"):
            try:
                email_config["recipients"] = [r.strip() for r in email_recipients_val.split(",")]
                logger.info("Loaded EMAIL_RECIPIENTS.")
            except Exception as e:
                logger.error(f"Error parsing EMAIL_RECIPIENTS from env/GCP: {str(e)}")
        elif not email_config.get("recipients"):
            logger.warning("EMAIL_RECIPIENTS not found in environment, GCP Secret Manager, or config file.")
            
        config["delivery"]["email"] = email_config

    # Slack configuration
    if "slack" in delivery_methods:
        slack_config = config["delivery"].get("slack", {})

        slack_webhook_url_val = os.environ.get("SLACK_WEBHOOK_URL")
        if not slack_webhook_url_val and use_gcp:
            slack_webhook_url_val = _get_secret_from_gcp("HN_SUMMARIZER_SLACK_WEBHOOK_URL")
        if slack_webhook_url_val and not slack_config.get("webhook_url"):
            slack_config["webhook_url"] = slack_webhook_url_val
            logger.info("Loaded SLACK_WEBHOOK_URL.")
        elif not slack_config.get("webhook_url"):
            logger.warning("SLACK_WEBHOOK_URL not found in environment, GCP Secret Manager, or config file.")

        slack_channel_val = os.environ.get("SLACK_CHANNEL")
        if not slack_channel_val and use_gcp:
            slack_channel_val = _get_secret_from_gcp("HN_SUMMARIZER_SLACK_CHANNEL")
        if slack_channel_val and not slack_config.get("channel"):
            slack_config["channel"] = slack_channel_val
            logger.info("Loaded SLACK_CHANNEL.")
        # No warning if channel is not found, as it might be optional

        config["delivery"]["slack"] = slack_config
