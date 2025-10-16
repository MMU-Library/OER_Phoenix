import requests
import os
from django.conf import settings
from resources.models import OERResource

TALIS_API_URL = "https://rl.talis.com/3/"

class TalisClient:
    def __init__(self):
        self.tenant = os.getenv('TALIS_TENANT')
        self.client_id = os.getenv('TALIS_CLIENT_ID')
        self.client_secret = os.getenv('TALIS_CLIENT_SECRET')
        self.access_token = None
    
    def authenticate(self):
        url = "https://users.talis.com/oauth/tokens"
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://rl.talis.com/3/'
        }
        response = requests.post(url, data=payload)
        response.raise_for_status()
        self.access_token = response.json()['access_token']
        return self.access_token
    
    def create_reading_list(self, title, description, resources):
        if not self.access_token:
            self.authenticate()
            
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/vnd.api+json'
        }
        
        # Create reading list
        list_data = {
            "data": {
                "type": "lists",
                "attributes": {
                    "title": title,
                    "description": description,
                    "visibility": "PUBLIC"
                }
            }
        }
        list_url = f"{TALIS_API_URL}{self.tenant}/lists"
        list_response = requests.post(list_url, json=list_data, headers=headers)
        list_response.raise_for_status()
        list_id = list_response.json()['data']['id']
        
        # Add resources
        items_url = f"{TALIS_API_URL}{self.tenant}/lists/{list_id}/items"
        for resource in resources:
            item_data = {
                "data": {
                    "type": "items",
                    "attributes": {
                        "uri": resource.url,
                        "meta": {
                            "title": resource.title,
                            "abstract": resource.description[:500]  # Truncate if needed
                        }
                    }
                }
            }
            item_response = requests.post(items_url, json=item_data, headers=headers)
            item_response.raise_for_status()
        
        return list_id
