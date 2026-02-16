import os
import requests
from typing import Optional

def clear_cache(pattern: str = 'campaigns:*', api_url: str = 'http://localhost:3000') -> bool:
    """
    Clears the Redis cache for the given pattern by calling the admin API.
    
    Args:
        pattern (str): Redis key pattern to clear (default: 'campaigns:*')
        api_url (str): Base URL of the API (default: 'http://localhost:3000')
        
    Returns:
        bool: True if successful, False otherwise.
    """
    cron_secret = os.getenv('CRON_SECRET')
    
    if not cron_secret:
        print("⚠️ CRON_SECRET not found in environment. Skipping cache invalidation.")
        return False
        
    endpoint = f"{api_url}/api/admin/cache-invalidation"
    
    try:
        response = requests.post(
            endpoint,
            json={'pattern': pattern},
            headers={
                'Content-Type': 'application/json',
                'x-admin-key': cron_secret
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Cache cleared successfully for pattern: {pattern}")
            return True
        else:
            print(f"❌ Failed to clear cache. Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error clearing cache: {str(e)}")
        return False
