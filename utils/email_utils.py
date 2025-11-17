"""
Email utilities using SendGrid API (HTTP-based, no SMTP timeouts)
Supports registration and voting link emails
"""
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
from typing import List

load_dotenv()

# SendGrid config from environment
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")  # Your SG. key from Render env
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "emmanuelnnanna.en@gmail.com")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5500")

def send_email(recipient: str, subject: str, body: str, html: bool = True) -> bool:
    """
    Send an email using SendGrid API
    Args:
        recipient: Email address of the recipient
        subject: Email subject line
        body: Email body content (HTML or plain)
        html: Whether the body is HTML (default True)
    Returns:
        True if email sent successfully, False otherwise
    """
    if not SENDGRID_API_KEY:
        print("❌ SENDGRID_API_KEY not set in environment")
        return False
    
    try:
        print(f"📧 Attempting to send email to {recipient} via SendGrid API...")
        print(f"📧 From: {SENDER_EMAIL}")
        
        # Create SendGrid message
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=recipient,
            subject=subject,
            html_content=body if html else None,
            plain_text_content=body if not html else None
        )
        
        # Send via API
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        if response.status_code == 202:
            print(f"✅ Email sent successfully to {recipient} (Status: {response.status_code})")
            return True
        else:
            print(f"❌ SendGrid API failed: Status {response.status_code}, Body: {response.body}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to send email to {recipient}: {e}")
        return False

def send_voting_link_email(recipient: str, election_title: str, voting_token: str) -> bool:
    """
    Send a one-time voting link to a registered voter via SendGrid API
    """
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
                    <strong>⚠️ Important Rules:</strong>
                    <ul>
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
    Send voting links to multiple voters via SendGrid API
    Args:
        recipients_tokens: List of tuples (email, token)
        election_title: Title of the election
    Returns:
        Dictionary with success/failure counts
    """
    results = {"success": 0, "failed": 0, "failed_emails": []}
    
    print(f"\n📧 Starting bulk email send to {len(recipient_tokens)} recipients via SendGrid API...")
    
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
    Send a confirmation email after successful registration via SendGrid API
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
# FORCE NEW COMMIT — SENDGRID API IS ACTIVE NOW