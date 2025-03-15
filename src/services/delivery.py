"""
Service for delivering summaries to various platforms.
"""
import logging
import time
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
import requests
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class DeliveryMethod(ABC):
    """Abstract base class for delivery methods."""
    
    @abstractmethod
    def send(self, summaries: List[Dict[str, Any]]) -> bool:
        """Send summaries using the delivery method."""
        pass

class EmailDelivery(DeliveryMethod):
    """Email delivery method."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Email delivery method.
        
        Args:
            config: Email configuration dictionary
        """
        self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.username = config.get('username')
        self.password = config.get('password')
        self.sender = config.get('sender', self.username)
        self.recipients = config.get('recipients', [])
        self.subject_template = config.get('subject_template', 'Hacker News Top Stories - {date}')
        
        if not self.username or not self.password:
            raise ValueError("Email username and password are required")
        
        if not self.recipients:
            raise ValueError("At least one recipient email is required")
    
    def send(self, summaries: List[Dict[str, Any]]) -> bool:
        """
        Send summaries via email.
        
        Args:
            summaries: List of summary dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = self.subject_template.format(
                date=time.strftime('%Y-%m-%d')
            )
            msg['From'] = self.sender
            msg['To'] = ', '.join(self.recipients)
            
            # Create plain text and HTML content
            text_content = self._create_text_content(summaries)
            html_content = self._create_html_content(summaries)
            
            # Attach parts
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Successfully sent email to {len(self.recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    def _create_text_content(self, summaries: List[Dict[str, Any]]) -> str:
        """Create plain text content for email."""
        content = f"Hacker News Top Stories - {time.strftime('%Y-%m-%d')}\n\n"
        
        for i, summary in enumerate(summaries, 1):
            story = summary.get('story', {})
            content += f"{i}. {story.get('title', 'Unknown Title')}\n"
            content += f"URL: {story.get('url', 'No URL')}\n"
            content += f"Points: {story.get('score', 0)} | "
            content += f"Comments: {story.get('descendants', 0)}\n\n"
            content += f"{summary.get('summary', 'No summary available')}\n\n"
            content += "-" * 80 + "\n\n"
        
        return content
    
    def _create_html_content(self, summaries: List[Dict[str, Any]]) -> str:
        """Create HTML content for email."""
        # Create CSS style as a separate string to avoid f-string issues with backslashes
        css_style = """
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                h1 { color: #2c3e50; }
                h2 { color: #3498db; margin-top: 20px; }
                .story { margin-bottom: 30px; border-bottom: 1px solid #eee; padding-bottom: 20px; }
                .meta { color: #7f8c8d; font-size: 0.9em; margin-bottom: 10px; }
                .summary { line-height: 1.8; }
                a { color: #3498db; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        """
        
        # Create HTML content with the date
        content = f"""
        <html>
        <head>
            {css_style}
        </head>
        <body>
            <h1>Hacker News Top Stories - {time.strftime('%Y-%m-%d')}</h1>
        """
        
        for i, summary in enumerate(summaries, 1):
            story = summary.get('story', {})
            content += f"""
            <div class="story">
                <h2>{i}. <a href="{story.get('url', '#')}">{story.get('title', 'Unknown Title')}</a></h2>
                <div class="meta">
                    Points: {story.get('score', 0)} | 
                    Comments: {story.get('descendants', 0)} | 
                    <a href="https://news.ycombinator.com/item?id={story.get('id', '')}">Discuss on HN</a>
                </div>
                <div class="summary">
                    {summary.get('summary', 'No summary available').replace('\n', '<br>')}
                </div>
            </div>
            """
        
        content += """
        </body>
        </html>
        """
        
        return content

class SlackDelivery(DeliveryMethod):
    """Slack delivery method."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Slack delivery method.
        
        Args:
            config: Slack configuration dictionary
        """
        self.webhook_url = config.get('webhook_url')
        self.channel = config.get('channel')
        self.username = config.get('username', 'HN Summarizer Bot')
        self.icon_emoji = config.get('icon_emoji', ':newspaper:')
        self.max_summaries_per_message = config.get('max_summaries_per_message', 3)
        
        if not self.webhook_url:
            raise ValueError("Slack webhook URL is required")
    
    def send(self, summaries: List[Dict[str, Any]]) -> bool:
        """
        Send summaries to Slack.
        
        Args:
            summaries: List of summary dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Split summaries into batches to avoid message size limits
            batches = [summaries[i:i + self.max_summaries_per_message] 
                      for i in range(0, len(summaries), self.max_summaries_per_message)]
            
            success = True
            for batch in batches:
                # Create message blocks
                blocks = self._create_message_blocks(batch)
                
                # Prepare payload
                payload = {
                    "channel": self.channel,
                    "username": self.username,
                    "icon_emoji": self.icon_emoji,
                    "blocks": blocks
                }
                
                # Send to Slack
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                response.raise_for_status()
                
                # Add delay between batches
                if len(batches) > 1:
                    time.sleep(1)
            
            logger.info(f"Successfully sent {len(summaries)} summaries to Slack")
            return success
            
        except requests.RequestException as e:
            logger.error(f"Error sending to Slack: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error in Slack delivery: {str(e)}")
            return False
    
    def _create_message_blocks(self, summaries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create Slack message blocks for summaries."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Hacker News Top Stories - {time.strftime('%Y-%m-%d')}",
                    "emoji": True
                }
            },
            {"type": "divider"}
        ]
        
        for summary in summaries:
            story = summary.get('story', {})
            
            # Add story header
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<{story.get('url', '#')}|{story.get('title', 'Unknown Title')}>*"
                }
            })
            
            # Add metadata
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Points: {story.get('score', 0)} | Comments: {story.get('descendants', 0)} | <https://news.ycombinator.com/item?id={story.get('id', '')}|Discuss on HN>"
                    }
                ]
            })
            
            # Add summary
            summary_text = summary.get('summary', 'No summary available')
            # Split long summaries into multiple blocks if needed
            if len(summary_text) > 3000:
                parts = [summary_text[i:i+3000] for i in range(0, len(summary_text), 3000)]
                for part in parts:
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": part
                        }
                    })
            else:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": summary_text
                    }
                })
            
            # Add divider
            blocks.append({"type": "divider"})
        
        return blocks

class LineDelivery(DeliveryMethod):
    """LINE delivery method."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LINE delivery method.
        
        Args:
            config: LINE configuration dictionary
        """
        self.access_token = config.get('access_token')
        self.to = config.get('to')  # User ID or group ID
        self.max_message_length = 5000  # LINE message length limit
        
        if not self.access_token:
            raise ValueError("LINE access token is required")
        
        if not self.to:
            raise ValueError("LINE recipient (user ID or group ID) is required")
    
    def send(self, summaries: List[Dict[str, Any]]) -> bool:
        """
        Send summaries to LINE.
        
        Args:
            summaries: List of summary dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create message content
            header = f"Hacker News Top Stories - {time.strftime('%Y-%m-%d')}\n\n"
            
            # Send header message
            self._send_line_message(header)
            
            # Send each summary as a separate message
            for i, summary in enumerate(summaries, 1):
                story = summary.get('story', {})
                
                message = f"{i}. {story.get('title', 'Unknown Title')}\n"
                message += f"URL: {story.get('url', 'No URL')}\n"
                message += f"Points: {story.get('score', 0)} | "
                message += f"Comments: {story.get('descendants', 0)}\n\n"
                message += f"{summary.get('summary', 'No summary available')}"
                
                # Split message if it's too long
                if len(message) > self.max_message_length:
                    parts = [message[i:i+self.max_message_length] 
                            for i in range(0, len(message), self.max_message_length)]
                    for part in parts:
                        self._send_line_message(part)
                        time.sleep(1)  # Avoid rate limiting
                else:
                    self._send_line_message(message)
                    time.sleep(1)  # Avoid rate limiting
            
            logger.info(f"Successfully sent {len(summaries)} summaries to LINE")
            return True
            
        except Exception as e:
            logger.error(f"Error sending to LINE: {str(e)}")
            return False
    
    def _send_line_message(self, message: str) -> None:
        """Send a message to LINE."""
        url = "https://api.line.me/v2/bot/message/push"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }
        
        payload = {
            "to": self.to,
            "messages": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()

class DeliveryService:
    """
    Service for delivering summaries to various platforms.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Delivery service.
        
        Args:
            config: Configuration dictionary for delivery
        """
        self.config = config
        self.method = self._initialize_delivery_method()
    
    def _initialize_delivery_method(self) -> DeliveryMethod:
        """Initialize the delivery method based on configuration."""
        method_name = self.config.get('method', 'email').lower()
        
        if method_name == 'email':
            return EmailDelivery(self.config.get('email', {}))
        elif method_name == 'slack':
            return SlackDelivery(self.config.get('slack', {}))
        elif method_name == 'line':
            return LineDelivery(self.config.get('line', {}))
        else:
            raise ValueError(f"Unsupported delivery method: {method_name}")
    
    def deliver(self, summaries: List[Dict[str, Any]]) -> bool:
        """
        Deliver summaries using the configured method.
        
        Args:
            summaries: List of summary dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Delivering {len(summaries)} summaries via {self.config.get('method', 'unknown')}")
            
            # Deliver using the initialized method
            success = self.method.send(summaries)
            
            if success:
                logger.info("Delivery completed successfully")
            else:
                logger.warning("Delivery completed with errors")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in delivery service: {str(e)}")
            return False
