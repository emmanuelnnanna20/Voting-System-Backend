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
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5500")

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
        print(f"📧 Attempting to send email to {recipient}...")
        print(f"📧 SMTP Server: {SMTP_SERVER}:{SMTP_PORT}")
        print(f"📧 From: {SENDER_EMAIL}")
        
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
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.set_debuglevel(1)  # Enable debug output
            server.starttls()  # Enable TLS encryption
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient, message.as_string())
        
        print(f"✅ Email sent successfully to {recipient}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication failed: {e}")
        print("⚠️ Check your SMTP_USERNAME and SMTP_PASSWORD in .env file")
        print("⚠️ For Gmail, you need an App Password, not your regular password")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error occurred: {e}")
        return False
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
    # CRITICAL: Use voting_page.html with token parameter
    voting_link = f"{FRONTEND_URL}/voting_page.html?token={voting_token}"
    
    subject = f"🗳️ Your Voting Link for {election_title}"
    
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ padding: 30px; background-color: #f9f9f9; }}
            .button {{ 
                display: inline-block; 
                padding: 15px 30px; 
                background-color: #4CAF50; 
                color: white !important; 
                text-decoration: none; 
                border-radius: 5px; 
                margin: 20px 0;
                font-weight: bold;
                font-size: 16px;
            }}
            .warning {{ 
                background-color: #fff3cd; 
                border: 2px solid #ffc107; 
                padding: 15px; 
                border-radius: 5px; 
                margin: 20px 0;
            }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            .link-box {{
                background-color: #fff;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
                word-break: break-all;
                margin: 15px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🗳️ Your Voting Link is Ready!</h1>
            </div>
            <div class="content">
                <h2>Hello Voter!</h2>
                <p>The election "<strong>{election_title}</strong>" is now active and ready for voting.</p>
                <p style="text-align: center;">
                    <a href="{voting_link}" class="button">🗳️ VOTE NOW</a>
                </p>
                
                <div class="warning">
                    <strong>⚠️ IMPORTANT:</strong>
                    <ul style="margin: 10px 0;">
                        <li>This is a <strong>ONE-TIME</strong> voting link</li>
                        <li>Once you vote, this link will <strong>EXPIRE</strong></li>
                        <li>You cannot change your vote after submission</li>
                        <li>Your vote is completely <strong>ANONYMOUS</strong></li>
                    </ul>
                </div>
                
                <p><strong>If the button doesn't work:</strong></p>
                <p>Copy and paste this link into your browser:</p>
                <div class="link-box">
                    <code>{voting_link}</code>
                </div>
                
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    This voting link was generated specifically for you. Do not share this link with anyone else.
                </p>
            </div>
            <div class="footer">
                <p>This is an automated message from VoteSecure Voting System</p>
                <p>Please do not reply to this email</p>
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
    
    print(f"\n📧 Starting bulk email send to {len(recipients_tokens)} recipients...")
    
    for email, token in recipients_tokens:
        print(f"\n📧 Sending to: {email}")
        if send_voting_link_email(email, election_title, token):
            results["success"] += 1
            print(f"✅ Success: {email}")
        else:
            results["failed"] += 1
            results["failed_emails"].append(email)
            print(f"❌ Failed: {email}")
    
    print(f"\n📊 Bulk send complete:")
    print(f"   ✅ Sent: {results['success']}")
    print(f"   ❌ Failed: {results['failed']}")
    
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
    subject = f"✅ Registration Confirmed: {election_title}"
    
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ padding: 30px; background-color: #f9f9f9; }}
            .success-box {{
                background-color: #d4edda;
                border: 2px solid #28a745;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
                text-align: center;
            }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✅ Registration Confirmed!</h1>
            </div>
            <div class="content">
                <h2>Hello!</h2>
                <p>You have successfully registered for the following election:</p>
                
                <div class="success-box">
                    <h3 style="margin: 0; color: #28a745;">"{election_title}"</h3>
                </div>
                
                <p><strong>What happens next?</strong></p>
                <ul>
                    <li>You will receive a <strong>voting link via email</strong> when the election starts</li>
                    <li>The voting link will be <strong>unique to you</strong> and can only be used once</li>
                    <li>Make sure to check your inbox (and spam folder) at the scheduled time</li>
                </ul>
                
                <p style="background-color: #fff3cd; padding: 15px; border-radius: 5px; border: 1px solid #ffc107;">
                    <strong>⚠️ Important:</strong> Keep an eye on your email inbox. The voting link will expire after use.
                </p>
                
                <p style="color: #666; margin-top: 30px;">
                    Thank you for registering! We'll notify you when it's time to vote.
                </p>
            </div>
            <div class="footer">
                <p>This is an automated message from VoteSecure Voting System</p>
                <p>Please do not reply to this email</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(recipient, subject, body, html=True)