# File: backend/app/utils/email.py
# Status: COMPLETE
# Dependencies: smtplib, email.mime, app.core.config

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

from app.core.config import settings

def send_email(
    recipient_email: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
    sender_email: Optional[str] = None,
    cc_recipients: Optional[List[str]] = None,
    bcc_recipients: Optional[List[str]] = None
) -> bool:
    """
    Send email using SMTP
    
    Args:
        recipient_email: Recipient email address
        subject: Email subject
        body_text: Plain text email body
        body_html: Optional HTML email body
        sender_email: Sender email address (defaults to settings)
        cc_recipients: Optional list of CC recipients
        bcc_recipients: Optional list of BCC recipients
        
    Returns:
        True if email sent successfully, False otherwise
    """
    # Use default sender if not provided
    if not sender_email:
        sender_email = settings.SMTP_SENDER
        
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient_email
    
    # Add CC recipients if provided
    if cc_recipients:
        message["Cc"] = ", ".join(cc_recipients)
        
    # Add text body
    text_part = MIMEText(body_text, "plain")
    message.attach(text_part)
    
    # Add HTML body if provided
    if body_html:
        html_part = MIMEText(body_html, "html")
        message.attach(html_part)
        
    # Get all recipients
    all_recipients = [recipient_email]
    if cc_recipients:
        all_recipients.extend(cc_recipients)
    if bcc_recipients:
        all_recipients.extend(bcc_recipients)
        
    try:
        # Connect to SMTP server
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            # Use TLS if enabled
            if settings.SMTP_TLS:
                server.starttls()
                
            # Login if credentials provided
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                
            # Send email
            server.sendmail(sender_email, all_recipients, message.as_string())
            
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False