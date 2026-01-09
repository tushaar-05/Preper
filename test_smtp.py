
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

smtp_server = os.environ.get('MAIL_SERVER')
smtp_port = int(os.environ.get('MAIL_PORT', 465))
smtp_user = os.environ.get('MAIL_USERNAME')
smtp_password = os.environ.get('MAIL_PASSWORD')
use_ssl = os.environ.get('MAIL_USE_SSL', 'False').lower() in ['true', '1', 't']

print(f"Testing SMTP Connection to: {smtp_server}:{smtp_port}")
print(f"User: {smtp_user}")
print(f"SSL: {use_ssl}")

try:
    if use_ssl:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
    else:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
    
    print("Connected to server.")
    
    print("Attempting login...")
    server.login(smtp_user, smtp_password)
    print("Login successful!")
    
    # Try sending a test email
    msg = f"Subject: Test Email\n\nThis is a test email from your Flask app debugger."
    server.sendmail(smtp_user, smtp_user, msg) # Send to self
    print(f"Test email sent to {smtp_user}")
    
    server.quit()
    print("Connection closed.")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
