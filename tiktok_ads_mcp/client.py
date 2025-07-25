"""TikTok Ads API Client for MCP Server"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin

from .config import config

# Set up logging
logger = logging.getLogger(__name__)

class TikTokAuthenticationError(Exception):
    """Raised when TikTok API authentication fails"""
    pass

class TikTokAPIError(Exception):
    """Raised when TikTok API requests fail"""
    pass

class TikTokAdsClient:
    """Enhanced TikTok Business API client with authentication validation and caching"""
    
    def __init__(self):
        """Initialize TikTok API client with comprehensive validation"""
        # Validate credentials on initialization
        if not config.validate_credentials():
            missing = config.get_missing_credentials()
            raise TikTokAuthenticationError(
                f"Missing required credentials: {', '.join(missing)}. "
                f"Please check your .env file and ensure all required fields are set."
            )
        
        self.app_id = config.APP_ID
        self.secret = config.SECRET
        self.access_token = config.ACCESS_TOKEN
        self.base_url = config.BASE_URL
        self.api_version = config.API_VERSION
        
        # Rate limiting
        self.rate_limit = config.API_RATE_LIMIT
        self.request_timeout = config.REQUEST_TIMEOUT
        self._last_request_time = 0
        self._request_count = 0
        self._rate_limit_window_start = time.time()
        
        # Test connection on initialization
        try:
            self._validate_connection()
            logger.info("TikTok API client initialized successfully")
        except Exception as e:
            logger.warning(f"TikTok API connection validation failed: {e}")
            # Don't raise here - allow graceful degradation
    
    def _validate_connection(self):
        """Test API connection with a lightweight call"""
        try:
            # Try to get advertisers as a connection test
            response = self._make_request('GET', '/advertiser/info/')
            if response.get('code') == 0:
                logger.info("TikTok API connection validated successfully")
            else:
                logger.warning(f"TikTok API returned non-zero code: {response.get('code')}")
        except Exception as e:
            logger.warning(f"Failed to validate TikTok API connection: {e}")
            raise TikTokAuthenticationError(f"Connection validation failed: {str(e)}")
    
    def _rate_limit_check(self):
        """Check and enforce rate limiting"""
        current_time = time.time()
        
        # Reset counter if we're in a new hour window
        if current_time - self._rate_limit_window_start > 3600:  # 1 hour
            self._request_count = 0
            self._rate_limit_window_start = current_time
        
        # Check if we've exceeded the rate limit
        if self._request_count >= self.rate_limit:
            sleep_time = 3600 - (current_time - self._rate_limit_window_start)
            logger.warning(f"Rate limit exceeded. Sleeping for {sleep_time:.1f} seconds")
            time.sleep(sleep_time)
            self._request_count = 0
            self._rate_limit_window_start = time.time()
        
        self._request_count += 1
        self._last_request_time = current_time
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None, use_cache: bool = True) -> Dict[str, Any]:
        """Make HTTP request to TikTok API with enhanced error handling and caching"""
        
        # Rate limiting
        self._rate_limit_check()
        
        # Check cache for GET requests
        if method == 'GET' and use_cache:
            cache_key = f"{endpoint}_{json.dumps(params or {}, sort_keys=True)}"
            cached_result = config.load_cached_data(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {endpoint}")
                return cached_result
        
        # Prepare request
        url = urljoin(f"{self.base_url}/{self.api_version}", endpoint.lstrip('/'))
        
        headers = {
            'Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }
        
        # Add app_id and secret to params for authentication
        if params is None:
            params = {}
        params.update({
            'app_id': self.app_id,
            'secret': self.secret
        })
        
        try:
            logger.debug(f"Making {method} request to {url}")
            
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=self.request_timeout)
            elif method == 'POST':
                response = requests.post(url, params=params, json=data, headers=headers, timeout=self.request_timeout)
            else:
                raise TikTokAPIError(f"Unsupported HTTP method: {method}")
            
            # Handle HTTP errors
            if response.status_code == 401:
                raise TikTokAuthenticationError("Invalid access token or credentials")
            elif response.status_code == 403:
                raise TikTokAuthenticationError("Access forbidden - check your API permissions")
            elif response.status_code == 429:
                raise TikTokAPIError("Rate limit exceeded - please try again later")
            elif response.status_code >= 400:
                raise TikTokAPIError(f"HTTP {response.status_code}: {response.text}")
            
            # Parse response
            try:
                result = response.json()
            except json.JSONDecodeError:
                raise TikTokAPIError(f"Invalid JSON response: {response.text}")
            
            # Check TikTok API response code
            if result.get('code') != 0:
                error_msg = result.get('message', 'Unknown API error')
                raise TikTokAPIError(f"TikTok API error {result.get('code')}: {error_msg}")
            
            # Cache successful GET responses
            if method == 'GET' and use_cache and result.get('code') == 0:
                cache_key = f"{endpoint}_{json.dumps(params or {}, sort_keys=True)}"
                config.save_cached_data(cache_key, result, ttl_minutes=5)
            
            return result
            
        except requests.exceptions.Timeout:
            raise TikTokAPIError(f"Request timeout after {self.request_timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise TikTokAPIError("Connection error - please check your internet connection")
        except requests.exceptions.RequestException as e:
            raise TikTokAPIError(f"Request failed: {str(e)}")
        except Exception as e:
            if isinstance(e, (TikTokAuthenticationError, TikTokAPIError)):
                raise
            raise TikTokAPIError(f"Unexpected error: {str(e)}")
    
    def health_check(self) -> bool:
        """Check if the API is accessible and credentials are valid"""
        try:
            response = self._make_request('GET', '/advertiser/info/', use_cache=False)
            return response.get('code') == 0
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def validate_token(self) -> Dict[str, Any]:
        """Validate access token and return detailed information"""
        try:
            response = self._make_request('GET', '/advertiser/info/', use_cache=False)
            
            if response.get('code') == 0:
                advertisers = response.get('data', {}).get('list', [])
                return {
                    "valid": True,
                    "advertiser_count": len(advertisers),
                    "message": "Access token is valid",
                    "advertisers": [
                        {
                            "advertiser_id": adv.get("advertiser_id"),
                            "advertiser_name": adv.get("advertiser_name", "Unknown"),
                            "status": adv.get("status", "Unknown")
                        }
                        for adv in advertisers[:5]  # Limit to first 5 for brevity
                    ]
                }
            else:
                return {
                    "valid": False,
                    "message": f"API returned code {response.get('code')}: {response.get('message', 'Unknown error')}"
                }
                
        except TikTokAuthenticationError as e:
            return {
                "valid": False,
                "message": f"Authentication error: {str(e)}"
            }
        except Exception as e:
            return {
                "valid": False,
                "message": f"Validation failed: {str(e)}"
            }
    
    def get_advertisers(self) -> List[Dict[str, Any]]:
        """Get all advertiser accounts"""
        try:
            response = self._make_request('GET', '/advertiser/info/')
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
        except Exception as e:
            logger.error(f"Failed to get advertisers: {e}")
            raise
    
    def get_campaigns(self, advertiser_id: str, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get campaigns for an advertiser"""
        params = {
            'advertiser_id': advertiser_id,
            'fields': json.dumps([
                "campaign_id", "campaign_name", "advertiser_id", "budget",
                "budget_mode", "status", "objective_type", "operation_status",
                "create_time", "modify_time", "campaign_type"
            ])
        }
        
        # Add filters if provided
        if filters:
            if 'campaign_ids' in filters:
                params['campaign_ids'] = json.dumps(filters['campaign_ids'])
            if 'status' in filters:
                params['primary_status'] = filters['status']
        
        try:
            response = self._make_request('GET', '/campaign/get/', params)
            campaigns = response.get('data', {}).get('list', [])
            
            return [
                {
                    "campaign_id": camp.get("campaign_id"),
                    "campaign_name": camp.get("campaign_name", "Unknown"),
                    "advertiser_id": camp.get("advertiser_id"),
                    "objective_type": camp.get("objective_type", "Unknown"),
                    "budget": float(camp.get("budget", 0)),
                    "budget_mode": camp.get("budget_mode", "Unknown"),
                    "status": camp.get("status", "Unknown"),
                    "operation_status": camp.get("operation_status", "Unknown"),
                    "campaign_type": camp.get("campaign_type", "REGULAR_CAMPAIGN"),
                    "create_time": camp.get("create_time"),
                    "modify_time": camp.get("modify_time")
                }
                for camp in campaigns
            ]
        except Exception as e:
            logger.error(f"Failed to get campaigns: {e}")
            raise
    
    def get_insights(self, advertiser_id: str, start_date: str, end_date: str,
                    data_level: str = "AUCTION_CAMPAIGN", metrics: List[str] = None,
                    object_ids: List[str] = None) -> List[Dict[str, Any]]:
        """Get performance insights"""
        if metrics is None:
            metrics = ["spend", "impressions", "clicks", "ctr", "cpm", "cpc", "conversions", "conversion_rate"]
        
        params = {
            'advertiser_id': advertiser_id,
            'data_level': data_level,
            'start_date': start_date,
            'end_date': end_date,
            'metrics': json.dumps(metrics),
            'page_size': 1000
        }
        
        # Add object IDs if specified
        if object_ids:
            if data_level == "AUCTION_CAMPAIGN":
                params['campaign_ids'] = json.dumps(object_ids)
            elif data_level == "AUCTION_ADGROUP":
                params['adgroup_ids'] = json.dumps(object_ids)
            elif data_level == "AUCTION_AD":
                params['ad_ids'] = json.dumps(object_ids)
        
        try:
            response = self._make_request('GET', '/report/integrated/get/', params)
            insights = response.get('data', {}).get('list', [])
            
            # Process and clean the insights data
            processed_insights = []
            for insight in insights:
                metrics_data = insight.get('metrics', {})
                dimensions = insight.get('dimensions', {})
                
                processed_insight = {
                    "stat_time_day": dimensions.get('stat_time_day'),
                    "campaign_id": dimensions.get('campaign_id'),
                    "campaign_name": dimensions.get('campaign_name'),
                    "adgroup_id": dimensions.get('adgroup_id'),
                    "adgroup_name": dimensions.get('adgroup_name'),
                    "ad_id": dimensions.get('ad_id'),
                    "ad_name": dimensions.get('ad_name')
                }
                
                # Add all requested metrics
                for metric in metrics:
                    value = metrics_data.get(metric)
                    if value is not None:
                        # Convert string numbers to float where appropriate
                        try:
                            if metric in ['spend', 'cpm', 'cpc']:
                                processed_insight[metric] = float(value)
                            elif metric in ['impressions', 'clicks', 'conversions']:
                                processed_insight[metric] = int(float(value))
                            elif metric in ['ctr', 'conversion_rate']:
                                processed_insight[metric] = float(value)
                            else:
                                processed_insight[metric] = value
                        except (ValueError, TypeError):
                            processed_insight[metric] = value
                    else:
                        processed_insight[metric] = 0
                
                # Remove None values from dimensions
                processed_insight = {k: v for k, v in processed_insight.items() if v is not None}
                processed_insights.append(processed_insight)
            
            return processed_insights
            
        except Exception as e:
            logger.error(f"Failed to get insights: {e}")
            raise 