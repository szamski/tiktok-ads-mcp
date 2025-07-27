"""TikTok Ads API Client for MCP Server"""

import requests
import json
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

from .config import config

# Set up logging
logger = logging.getLogger(__name__)

class TikTokAdsClient:
    """TikTok Business API client for campaign operations."""
    
    def __init__(self):
        """Initialize TikTok API client"""
        # Validate credentials on initialization
        if not config.validate_credentials():
            missing = config.get_missing_credentials()
            raise Exception(
                f"Missing required credentials: {', '.join(missing)}. "
                f"Please check your configuration and ensure all required fields are set."
            )
        
        self.app_id = config.APP_ID
        self.secret = config.SECRET
        self.access_token = config.ACCESS_TOKEN
        self.base_url = config.BASE_URL
        self.api_version = config.API_VERSION
        self.request_timeout = config.REQUEST_TIMEOUT
        
        logger.info("TikTok API client initialized")
    

    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to TikTok API with proper authentication handling"""
        
        # Prepare parameters
        if params is None:
            params = {}
        
        # Add app_id and secret ONLY for oauth2 endpoints
        if 'oauth2' in endpoint:
            params.update({
                'app_id': self.app_id,
                'secret': self.secret
            })
        
        # Construct URL exactly like the working curl command
        if params:
            from urllib.parse import urlencode
            query_string = urlencode(params)
            url = f"{self.base_url}/{self.api_version}/{endpoint}?{query_string}"
        else:
            url = f"{self.base_url}/{self.api_version}/{endpoint}"
        
        headers = {
            'Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }
        
        try:
            logger.debug(f"Making {method} request to {url}")
            logger.debug(f"Parameters: {params}")
            logger.debug(f"Headers: {headers}")
            
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=self.request_timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=self.request_timeout)
            else:
                raise Exception(f"Unsupported HTTP method: {method}")
            
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response text: {response.text}")
            
            # Handle HTTP errors
            if response.status_code == 401:
                raise Exception("Invalid access token or credentials")
            elif response.status_code == 403:
                raise Exception("Access forbidden - check your API permissions")
            elif response.status_code == 429:
                raise Exception("Rate limit exceeded - please try again later")
            elif response.status_code >= 400:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            # Parse response
            try:
                result = response.json()
            except json.JSONDecodeError:
                raise Exception(f"Invalid JSON response: {response.text}")
            
            # Check TikTok API response code
            if result.get('code') != 0:
                error_msg = result.get('message', 'Unknown API error')
                raise Exception(f"TikTok API error {result.get('code')}: {error_msg}")
            
            return result
            
        except requests.exceptions.Timeout:
            raise Exception(f"Request timeout after {self.request_timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise Exception("Connection error - please check your internet connection")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}") 