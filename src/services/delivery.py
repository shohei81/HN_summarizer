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
                .restricted { color: #95a5a6; font-style: italic; }
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
            # Format each summary using the existing method
            content += self._format_summary_for_email(summary, index=i)
        
        content += """
        </body>
        </html>
        """
        
        return content

    # メールテンプレート内の処理例を修正
    def _format_summary_for_email(self, summary, index=None):
        index_prefix = f"{index}. " if index is not None else ""
        story = summary.get('story', {})
        
        if summary.get('access_restricted', False):
            # アクセス制限のある記事は要約なしでタイトルとURLだけ表示
            return f"""
            <div class="story">
                <h2>{index_prefix}<a href="{story.get('url', '#')}">{story.get('title', 'Unknown Title')}</a></h2>
                <p class="restricted"><em>このコンテンツはアクセス制限があるため要約できませんでした。</em></p>
            </div>
            """
        else:
            # 通常の要約付き記事
            # Replace newlines with <br> tags before adding to the HTML
            summary_text = summary.get('summary', 'No summary available').replace('\n', '<br>')
            
            return f"""
            <div class="story">
                <h2>{index_prefix}<a href="{story.get('url', '#')}">{story.get('title', 'Unknown Title')}</a></h2>
                <div class="meta">
                    {story.get('by', '')} | 
                    <a href="https://news.ycombinator.com/item?id={story.get('id', '')}">Discuss on HN</a>
                </div>
                <div class="summary">
                    {summary_text}
                </div>
            </div>
            """

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
            # Add story header with title and URL
            story = summary.get('story', {})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<{story.get('url', '#')}|{story.get('title', 'Unknown Title')}>*"
                }
            })
            
            # Check if content is access restricted
            if summary.get('access_restricted', False):
                # Add a note about restricted access
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "_このコンテンツはアクセス制限があるため要約できませんでした。_"
                    }
                })
            else:
                # Add summary for accessible content
                summary_text = summary.get('summary', 'No summary available')
                # Split long summaries into multiple blocks if needed
                if len(summary_text) > 3000:
                    max_length = 3000
                    parts = []
                    for i in range(0, len(summary_text), max_length):
                        parts.append(summary_text[i:i+max_length])
                    
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
            
            # Add divider between stories
            blocks.append({"type": "divider"})
        
        return blocks

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
        self.methods = []
        self._initialize_delivery_methods()
    
    def _initialize_delivery_methods(self) -> None:
        """Initialize delivery methods based on configuration."""
        method_name = self.config.get('method', 'email').lower()
        
        # Support for multiple delivery methods (comma-separated)
        if ',' in method_name:
            method_names = [m.strip() for m in method_name.split(',')]
        else:
            method_names = [method_name]
        
        for name in method_names:
            if name == 'email':
                self.methods.append(EmailDelivery(self.config.get('email', {})))
            elif name == 'slack':
                self.methods.append(SlackDelivery(self.config.get('slack', {})))
            else:
                logger.warning(f"Unsupported delivery method: {name}")
    
    def deliver(self, summaries: List[Dict[str, Any]]) -> bool:
        """
        Deliver summaries using all configured methods.
        
        Args:
            summaries: List of summary dictionaries
            
        Returns:
            True if all deliveries were successful, False otherwise
        """
        if not self.methods:
            logger.error("No delivery methods configured")
            return False
        
        try:
            logger.info(f"Delivering {len(summaries)} summaries via {len(self.methods)} method(s)")
            
            # Track success of all delivery methods
            all_success = True
            
            # Deliver using each initialized method
            for method in self.methods:
                method_name = method.__class__.__name__
                logger.info(f"Delivering via {method_name}")
                
                success = method.send(summaries)
                if success:
                    logger.info(f"Delivery via {method_name} completed successfully")
                else:
                    logger.warning(f"Delivery via {method_name} failed")
                    all_success = False
            
            if all_success:
                logger.info("All deliveries completed successfully")
            else:
                logger.warning("Some deliveries failed")
            
            return all_success
            
        except Exception as e:
            logger.error(f"Error in delivery service: {str(e)}")
            return False
