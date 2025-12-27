import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get('MOJOAUTH_API_KEY')
print(f"Loaded API Key: {api_key}")

if not api_key:
    # Fallback to hardcoded if env var fails (just for test)
    api_key = "84f932c0-ef90-4516-8a84-be0dd834eca9"
    print(f"Using Hardcoded Key: {api_key}")

url = "https://api.mojoauth.com/users/emailotp"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": api_key
}
payload = {"email": "tusharsingh222555@gmail.com"} # Using your email

print(f"Sending request to {url}...")
try:
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Exception: {e}")
