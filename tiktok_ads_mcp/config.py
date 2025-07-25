"""Configuration management for TikTok Ads MCP Server"""

import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List
import json
from pathlib import Path

# Load .env file from the project root (parent of tiktok_ads_mcp package)
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(current_dir, '.env')
load_dotenv(dotenv_path)

class TikTokConfig:
    """Enhanced configuration class for TikTok Business API with secure local authentication"""
    
    # TikTok API Configuration
    APP_ID: str = os.getenv("TIKTOK_APP_ID", "")
    SECRET: str = os.getenv("TIKTOK_SECRET", "")
    ACCESS_TOKEN: str = os.getenv("TIKTOK_ACCESS_TOKEN", "")
    ADVERTISER_ID: str = os.getenv("TIKTOK_ADVERTISER_ID", "")
    SANDBOX: bool = os.getenv("TIKTOK_SANDBOX", "false").lower() == "true"
    
    # Token Caching Configuration (for performance optimization)
    TOKEN_CACHE_DIR: str = os.getenv("TOKEN_CACHE_DIR", os.path.join(current_dir, ".cache"))
    TOKEN_CACHE_ENABLED: bool = os.getenv("TOKEN_CACHE_ENABLED", "true").lower() == "true"
    
    # API URLs
    BASE_URL: str = "https://business-api.tiktok.com/open_api" if not SANDBOX else "https://sandbox-ads.tiktok.com/open_api"
    API_VERSION: str = "v1.3"
    
    # Rate Limiting Configuration
    API_RATE_LIMIT: int = int(os.getenv("TIKTOK_API_RATE_LIMIT", "1000"))  # requests per hour
    REQUEST_TIMEOUT: int = int(os.getenv("TIKTOK_REQUEST_TIMEOUT", "30"))  # seconds
    
    @classmethod
    def validate_credentials(cls) -> bool:
        """Validate that all required credentials are present"""
        required_fields = [cls.APP_ID, cls.SECRET, cls.ACCESS_TOKEN]
        return all(field.strip() for field in required_fields)
    
    @classmethod
    def get_missing_credentials(cls) -> List[str]:
        """Get list of missing credential fields"""
        missing = []
        if not cls.APP_ID.strip():
            missing.append("TIKTOK_APP_ID")
        if not cls.SECRET.strip():
            missing.append("TIKTOK_SECRET")
        if not cls.ACCESS_TOKEN.strip():
            missing.append("TIKTOK_ACCESS_TOKEN")
        return missing
    
    @classmethod
    def get_auth_info(cls) -> Dict[str, Any]:
        """Get comprehensive authentication information"""
        missing = cls.get_missing_credentials()
        return {
            "has_credentials": len(missing) == 0,
            "missing_credentials": missing,
            "has_app_id": bool(cls.APP_ID.strip()),
            "has_secret": bool(cls.SECRET.strip()),
            "has_access_token": bool(cls.ACCESS_TOKEN.strip()),
            "has_advertiser_id": bool(cls.ADVERTISER_ID.strip()),
            "sandbox_mode": cls.SANDBOX,
            "cache_enabled": cls.TOKEN_CACHE_ENABLED,
            "cache_dir": cls.TOKEN_CACHE_DIR,
            "rate_limit": cls.API_RATE_LIMIT,
            "request_timeout": cls.REQUEST_TIMEOUT
        }
    
    @classmethod
    def get_health_info(cls) -> Dict[str, Any]:
        """Get system health information"""
        cache_dir_exists = os.path.exists(cls.TOKEN_CACHE_DIR)
        cache_writable = False
        
        if cache_dir_exists:
            try:
                test_file = os.path.join(cls.TOKEN_CACHE_DIR, ".test_write")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                cache_writable = True
            except Exception:
                cache_writable = False
        
        return {
            "config_valid": cls.validate_credentials(),
            "cache_dir_exists": cache_dir_exists,
            "cache_writable": cache_writable,
            "env_file_exists": os.path.exists(dotenv_path),
            "base_url": cls.BASE_URL,
            "api_version": cls.API_VERSION
        }
    
    @classmethod
    def save_cached_data(cls, key: str, data: Any, ttl_minutes: int = 5) -> bool:
        """Save data to cache with TTL"""
        if not cls.TOKEN_CACHE_ENABLED:
            return False
            
        try:
            # Create cache directory if it doesn't exist
            os.makedirs(cls.TOKEN_CACHE_DIR, exist_ok=True)
            
            # Prepare cache entry
            import time
            cache_entry = {
                "data": data,
                "timestamp": time.time(),
                "ttl_minutes": ttl_minutes
            }
            
            # Save to file
            cache_file = os.path.join(cls.TOKEN_CACHE_DIR, f"{key}.json")
            with open(cache_file, 'w') as f:
                json.dump(cache_entry, f, default=str)
            
            # Set restrictive permissions (owner read/write only)
            os.chmod(cache_file, 0o600)
            return True
            
        except Exception as e:
            print(f"Failed to save cache: {e}")
            return False
    
    @classmethod
    def load_cached_data(cls, key: str) -> Optional[Any]:
        """Load data from cache if not expired"""
        if not cls.TOKEN_CACHE_ENABLED:
            return None
            
        try:
            cache_file = os.path.join(cls.TOKEN_CACHE_DIR, f"{key}.json")
            
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'r') as f:
                cache_entry = json.load(f)
            
            # Check if expired
            import time
            age_minutes = (time.time() - cache_entry["timestamp"]) / 60
            
            if age_minutes > cache_entry.get("ttl_minutes", 5):
                # Remove expired cache
                os.remove(cache_file)
                return None
            
            return cache_entry["data"]
            
        except Exception:
            return None

# Global config instance
config = TikTokConfig() 