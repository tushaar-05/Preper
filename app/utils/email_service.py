"""
Email Service Utility
Handles sending OTP emails and other email communications
"""
from flask import current_app
from flask_mail import Mail, Message
import requests
import json
import os

mail = Mail()

def init_mail(app):
    """Initialize Flask-Mail with the app"""
    mail.init_app(app)



def send_mojoauth_otp(email):
    """
    Send OTP via MojoAuth API
    
    Args:
        email (str): Recipient email address
    
    Returns:
        str: state_id if successful, None otherwise
    """
    api_key = current_app.config.get('MOJOAUTH_API_KEY')
    if not api_key:
        print("Error: MOJOAUTH_API_KEY not found in config")
        return None

    try:
        url = "https://api.mojoauth.com/users/emailotp"
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }
        payload = {"email": email}
        
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        
        if response.status_code == 200 or response.status_code == 201:
            return data.get('state_id')
        else:
            print(f"Error sending MojoAuth OTP: {data}")
            return None
            
    except Exception as e:
        print(f"Exception sending MojoAuth OTP: {str(e)}")
        return None

def verify_mojoauth_otp(state_id, otp):
    """
    Verify OTP via MojoAuth API
    
    Args:
        state_id (str): The state_id received during sending
        otp (str): The OTP entered by user
        
    Returns:
        bool: True if valid, False otherwise
    """
    api_key = current_app.config.get('MOJOAUTH_API_KEY')
    if not api_key:
        return False
        
    try:
        url = "https://api.mojoauth.com/users/emailotp/verify"
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }
        payload = {
            "state_id": state_id,
            "otp": otp
        }
        
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        
        if response.status_code == 200 and data.get('authenticated'):
            return True
        else:
            print(f"MojoAuth Verification Failed: {data}")
            return False
            
    except Exception as e:
        print(f"Exception verifying MojoAuth OTP: {str(e)}")
        return False

def send_otp_email(email, otp_code, purpose='login'):
    """
    Send OTP email to user
    
    Args:
        email (str): Recipient email address
        otp_code (str): 6-digit OTP code
        purpose (str): 'login' or 'register'
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = f"Your PREPER {'Registration' if purpose == 'register' else 'Login'} OTP"
        
        # HTML email template
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background-color: #000000;
                    color: #ffffff;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 40px 20px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                }}
                .logo {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #9685fe;
                    letter-spacing: 1px;
                }}
                .content {{
                    background: linear-gradient(135deg, #1a1a1a 0%, #0a0a0a 100%);
                    border: 1px solid rgba(150, 133, 254, 0.2);
                    border-radius: 16px;
                    padding: 40px;
                    text-align: center;
                }}
                .title {{
                    font-size: 24px;
                    font-weight: 600;
                    margin-bottom: 16px;
                    color: #ffffff;
                }}
                .message {{
                    font-size: 16px;
                    color: #a0a0a0;
                    margin-bottom: 32px;
                    line-height: 1.6;
                }}
                .otp-box {{
                    background: rgba(150, 133, 254, 0.1);
                    border: 2px solid #9685fe;
                    border-radius: 12px;
                    padding: 24px;
                    margin: 32px 0;
                }}
                .otp-code {{
                    font-size: 48px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    color: #9685fe;
                    font-family: 'Courier New', monospace;
                }}
                .expiry {{
                    font-size: 14px;
                    color: #808080;
                    margin-top: 24px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding-top: 24px;
                    border-top: 1px solid #2a2a2a;
                    color: #606060;
                    font-size: 14px;
                }}
                .warning {{
                    background: rgba(255, 193, 7, 0.1);
                    border-left: 3px solid #ffc107;
                    padding: 16px;
                    margin-top: 24px;
                    border-radius: 4px;
                    font-size: 14px;
                    color: #ffc107;
                    text-align: left;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">PREPER</div>
                </div>
                
                <div class="content">
                    <div class="title">
                        {'Welcome to PREPER!' if purpose == 'register' else 'Login Verification'}
                    </div>
                    
                    <div class="message">
                        {'Complete your registration by entering the OTP below.' if purpose == 'register' else 'Use the OTP below to login to your account.'}
                    </div>
                    
                    <div class="otp-box">
                        <div class="otp-code">{otp_code}</div>
                    </div>
                    
                    <div class="expiry">
                        This OTP will expire in 10 minutes
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong> Never share this OTP with anyone. PREPER staff will never ask for your OTP.
                    </div>
                </div>
                
                <div class="footer">
                    <p>If you didn't request this OTP, please ignore this email.</p>
                    <p>© 2025 PREPER. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text fallback
        text_body = f"""
        PREPER {'Registration' if purpose == 'register' else 'Login'} OTP
        
        Your OTP code is: {otp_code}
        
        This OTP will expire in 10 minutes.
        
        If you didn't request this OTP, please ignore this email.
        
        © 2025 PREPER. All rights reserved.
        """
        
        # Try Resend first
        # Try Resend first
        api_key = current_app.config.get('RESEND_API_KEY')
        print(f"DEBUG: Resend API Key present: {bool(api_key)}")
        
        if api_key:
            try:
                print(f"DEBUG: Attempting to send via Resend to {email}...")
                resend.api_key = api_key
                params = {
                    "from": "PREPER <onboarding@resend.dev>",
                    "to": [email],
                    "subject": subject,
                    "html": html_body,
                    "text": text_body
                }
                response = resend.Emails.send(params)
                print(f"DEBUG: Resend Response: {response}")
                return True
            except Exception as e:
                print(f"DEBUG: Resend failed, falling back to SMTP: {e}")

        msg = Message(
            subject=subject,
            recipients=[email],
            html=html_body,
            body=text_body
        )
        
        mail.send(msg)
        return True
        
    except Exception as e:
        print(f"Error sending OTP email: {str(e)}")
        # In development, if email fails, print OTP to console and return True so we can test the flow
        if current_app.debug or current_app.testing:
            print(f"\n{'='*50}\n[DEV MODE] Email Failure Fallback\nOTP Code: {otp_code}\n{'='*50}\n")
            return True
        return False

def send_welcome_email(email, full_name):
    """
    Send welcome email after successful registration
    
    Args:
        email (str): Recipient email address
        full_name (str): User's full name
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = "Welcome to PREPER - Your NST Preparation Journey Begins!"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background-color: #000000;
                    color: #ffffff;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 40px 20px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                }}
                .logo {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #9685fe;
                    letter-spacing: 1px;
                }}
                .content {{
                    background: linear-gradient(135deg, #1a1a1a 0%, #0a0a0a 100%);
                    border: 1px solid rgba(150, 133, 254, 0.2);
                    border-radius: 16px;
                    padding: 40px;
                }}
                .title {{
                    font-size: 28px;
                    font-weight: 600;
                    margin-bottom: 16px;
                    color: #ffffff;
                    text-align: center;
                }}
                .greeting {{
                    font-size: 18px;
                    color: #a0a0a0;
                    margin-bottom: 24px;
                }}
                .feature {{
                    margin: 16px 0;
                    padding-left: 24px;
                    position: relative;
                }}
                .feature:before {{
                    content: "✓";
                    position: absolute;
                    left: 0;
                    color: #9685fe;
                    font-weight: bold;
                }}
                .cta {{
                    text-align: center;
                    margin-top: 32px;
                }}
                .button {{
                    display: inline-block;
                    background-color: #9685fe;
                    color: #ffffff;
                    padding: 14px 32px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: 600;
                    margin-top: 16px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding-top: 24px;
                    border-top: 1px solid #2a2a2a;
                    color: #606060;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">PREPER</div>
                </div>
                
                <div class="content">
                    <div class="title">Welcome Aboard! 🎉</div>
                    
                    <div class="greeting">
                        Hi {full_name},
                    </div>
                    
                    <p>We're thrilled to have you join PREPER! You've taken the first step towards acing your NST preparation.</p>
                    
                    <h3 style="color: #9685fe; margin-top: 32px;">What's Next?</h3>
                    
                    <div class="feature">Access comprehensive study materials</div>
                    <div class="feature">Take mock tests to track your progress</div>
                    <div class="feature">Get expert mentorship from NST students</div>
                    <div class="feature">Connect with peers in our community</div>
                    
                    <div class="cta">
                        <p style="color: #a0a0a0;">Ready to start your journey?</p>
                        <a href="http://127.0.0.1:5005/login" class="button">Go to Dashboard</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Need help? Contact us at contact@preper.com</p>
                    <p>© 2025 PREPER. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Welcome to PREPER!
        
        Hi {full_name},
        
        We're thrilled to have you join PREPER! You've taken the first step towards acing your NST preparation.
        
        What's Next?
        ✓ Access comprehensive study materials
        ✓ Take mock tests to track your progress
        ✓ Get expert mentorship from NST students
        ✓ Connect with peers in our community
        
        Ready to start your journey? Login at: http://127.0.0.1:5005/login
        
        Need help? Contact us at contact@preper.com
        
        © 2025 PREPER. All rights reserved.
        """
        
        # Try Resend first
        if current_app.config.get('RESEND_API_KEY'):
            try:
                resend.api_key = current_app.config['RESEND_API_KEY']
                params = {
                    "from": "PREPER <onboarding@resend.dev>",
                    "to": [email],
                    "subject": subject,
                    "html": html_body,
                    "text": text_body
                }
                resend.Emails.send(params)
                return True
            except Exception as e:
                print(f"Resend failed, falling back to SMTP: {e}")

        msg = Message(
            subject=subject,
            recipients=[email],
            html=html_body,
            body=text_body
        )
        
        mail.send(msg)
        return True
        
    except Exception as e:
        print(f"Error sending welcome email: {str(e)}")
        return False
