"""
Email utilities for sending registration and voting links
Supports SMTP configuration via environment variables
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from typing import List

load_dotenv()

# Email configuration from environment variables
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "your-email@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your-app-password")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", SMTP_USERNAME)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

def send_email(recipient: str, subject: str, body: str, html: bool = True) -> bool:
    """
    Send an email using SMTP
    Args:
        recipient: Email address of the recipient
        subject: Email subject line
        body: Email body content
        html: Whether the body is HTML (default True)
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = SENDER_EMAIL
        message["To"] = recipient
        
        # Attach body
        if html:
            part = MIMEText(body, "html")
        else:
            part = MIMEText(body, "plain")
        message.attach(part)
        
        # Connect to SMTP server and send
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Enable TLS encryption
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient, message.as_string())
        
        print(f"✅ Email sent successfully to {recipient}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email to {recipient}: {e}")
        return False

def send_voting_link_email(recipient: str, election_title: str, voting_token: str) -> bool:
    """
    Send a one-time voting link to a registered voter
    Args:
        recipient: Voter's email address
        election_title: Title of the election
        voting_token: Unique token for this voter's voting link
    Returns:
        True if email sent successfully
    """
    # IMPORTANT: Use voting_page.html with token parameter
    voting_link = f"{FRONTEND_URL}/voting_page.html?token={voting_token}"
    
    subject = f"Your Voting Link for {election_title}"
    
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .button {{ display: inline-block; padding: 12px 24px; background-color: #4CAF50; 
                      color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
            .warning {{ color: #d32f2f; font-weight: bold; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🗳️ Your Voting Link is Ready!</h1>
            </div>
            <div class="content">
                <h2>Hello!</h2>
                <p>The election "<strong>{election_title}</strong>" has started.</p>
                <p>Click the button below to cast your vote:</p>
                <p style="text-align: center;">
                    <a href="{voting_link}" class="button">Vote Now</a>
                </p>
                <p class="warning">⚠️ Important: This is a ONE-TIME link. Once you vote, 
                this link will become invalid.</p>
                <p>If the button doesn't work, copy and paste this link into your browser:</p>
                <p style="word-break: break-all; background-color: #fff; padding: 10px; border: 1px solid #ddd;">
                    {voting_link}
                </p>
            </div>
            <div class="footer">
                <p>This is an automated message from VoteSecure. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(recipient, subject, body, html=True)

def send_bulk_voting_links(recipients_tokens: List[tuple], election_title: str) -> dict:
    """
    Send voting links to multiple voters
    Args:
        recipients_tokens: List of tuples (email, token)
        election_title: Title of the election
    Returns:
        Dictionary with success/failure counts
    """
    results = {"success": 0, "failed": 0, "failed_emails": []}
    
    for email, token in recipients_tokens:
        if send_voting_link_email(email, election_title, token):
            results["success"] += 1
        else:
            results["failed"] += 1
            results["failed_emails"].append(email)
    
    return results

def send_registration_confirmation(recipient: str, election_title: str) -> bool:
    """
    Send a confirmation email after successful registration
    Args:
        recipient: Voter's email address
        election_title: Title of the election
    Returns:
        True if email sent successfully
    """
    subject = f"Registration Confirmed: {election_title}"
    
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✅ Registration Confirmed</h1>
            </div>
            <div class="content">
                <h2>Hello!</h2>
                <p>You have successfully registered for the election:</p>
                <h3>{election_title}</h3>
                <p>You will receive a voting link via email when the election starts.</p>
                <p><strong>Please check your inbox</strong> at the scheduled time to cast your vote.</p>
            </div>
            <div class="footer">
                <p>This is an automated message from VoteSecure. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(recipient, subject, body, html=True)