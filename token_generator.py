import requests
import os
from dotenv import load_dotenv

load_dotenv()

def generate_token():
    """Generate Amadeus API token"""
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "client_credentials",
        "client_id": os.getenv('AMADEUS_API_KEY'),
        "client_secret": os.getenv('AMADEUS_API_SECRET')
    }
    
    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            token_data = response.json()
            if token_data.get('state') == 'approved':
                return token_data.get('access_token')
        print(f"Error generating token: {response.status_code}")
        print(response.json())
        return None
    except Exception as e:
        print(f"Error in token generation: {str(e)}")
        return None 