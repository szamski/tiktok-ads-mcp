"""Get Authorized Ad Accounts Tool"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def get_authorized_ad_accounts(client, **kwargs) -> List[Dict[str, Any]]:
    """Get all authorized ad accounts"""
    try:
        response = client._make_request('GET', 'oauth2/advertiser/get/')
        
        if response.get('code') == 0:
            advertisers = response.get('data', {}).get('list', [])
            
            return [
                {
                    "advertiser_id": adv.get("advertiser_id"),
                    "advertiser_name": adv.get("advertiser_name", "Unknown"),
                    "status": adv.get("status", "Unknown"),
                    "company": adv.get("company", ""),
                    "country": adv.get("country", ""),
                    "currency": adv.get("currency", ""),
                    "timezone": adv.get("timezone", "")
                }
                for adv in advertisers
            ]
        else:
            raise Exception(f"API returned code {response.get('code')}: {response.get('message', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Failed to get advertisers: {e}")
        raise 