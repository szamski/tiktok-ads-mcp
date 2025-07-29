#!/usr/bin/env python3
"""TikTok Ads MCP Server

A modern MCP server implementation for TikTok Business API integration using FastMCP.
This provides a clean, efficient interface to the TikTok Ads API with automatic schema generation.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

# MCP imports
from mcp.server import FastMCP
from mcp.server.fastmcp import Context

# TikTok client
from .client import TikTokAdsClient
from .config import config
from .tools import (
    get_business_centers,
    get_authorized_ad_accounts,
    get_campaigns,
    get_ad_groups,
    get_ads,
    get_reports
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global client instance (will be initialized on first use)
tiktok_client: Optional[TikTokAdsClient] = None

# Create MCP server instance
app = FastMCP("tiktok-ads")

def get_tiktok_client() -> TikTokAdsClient:
    """Get or create TikTok API client instance"""
    global tiktok_client
    
    if tiktok_client is None:
        try:
            tiktok_client = TikTokAdsClient()
            logger.info("TikTok API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TikTok client: {e}")
            raise
    
    return tiktok_client

@app.tool()
def get_business_centers_tool(bc_id: str = "", page: int = 1, page_size: int = 10) -> str:
    """Get business centers accessible by the current access token"""
    try:
        client = get_tiktok_client()
        centers = get_business_centers(client, bc_id=bc_id, page=page, page_size=page_size)
        
        return json.dumps({
            "success": True,
            "count": len(centers),
            "centers": centers
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "error": True,
            "message": f"Error: {str(e)}",
            "suggestion": "Please check your configuration and try again."
        }, indent=2)

@app.tool()
def get_authorized_ad_accounts_tool(random_string: str = "") -> str:
    """Get all authorized ad accounts accessible by the current access token"""
    try:
        client = get_tiktok_client()
        advertisers = get_authorized_ad_accounts(client)
        
        return json.dumps({
            "success": True,
            "count": len(advertisers),
            "advertisers": advertisers
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "error": True,
            "message": f"Error: {str(e)}",
            "suggestion": "Please check your configuration and try again."
        }, indent=2)

@app.tool()
def get_campaigns_tool(advertiser_id: str, filters: Dict = None) -> str:
    """Get campaigns for a specific advertiser with optional filtering"""
    if not advertiser_id:
        raise ValueError("advertiser_id is required")
    
    try:
        client = get_tiktok_client()
        campaigns = get_campaigns(client, advertiser_id=advertiser_id, filters=filters or {})
        
        return json.dumps({
            "success": True,
            "advertiser_id": advertiser_id,
            "count": len(campaigns),
            "campaigns": campaigns
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "error": True,
            "message": f"Error: {str(e)}",
            "suggestion": "Please check your configuration and try again."
        }, indent=2)

@app.tool()
def get_ad_groups_tool(
    advertiser_id: str, 
    campaign_id: Optional[str] = None, 
    filters: Dict = None, 
    page: int = 1, 
    page_size: int = 10
) -> str:
    """Get ad groups for a specific advertiser with optional filtering"""
    if not advertiser_id:
        raise ValueError("advertiser_id is required")
    
    try:
        client = get_tiktok_client()
        ad_groups = get_ad_groups(client, advertiser_id=advertiser_id, campaign_id=campaign_id, filters=filters or {})
        
        return json.dumps({
            "success": True,
            "advertiser_id": advertiser_id,
            "campaign_id": campaign_id,
            "count": len(ad_groups),
            "ad_groups": ad_groups
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "error": True,
            "message": f"Error: {str(e)}",
            "suggestion": "Please check your configuration and try again."
        }, indent=2)

@app.tool()
def get_ads_tool(
    advertiser_id: str, 
    adgroup_id: Optional[str] = None, 
    filters: Dict = None, 
    page: int = 1, 
    page_size: int = 10
) -> str:
    """Get ads for a specific advertiser with optional filtering"""
    if not advertiser_id:
        raise ValueError("advertiser_id is required")
    
    try:
        client = get_tiktok_client()
        ads = get_ads(client, advertiser_id=advertiser_id, adgroup_id=adgroup_id, filters=filters or {})
        
        return json.dumps({
            "success": True,
            "advertiser_id": advertiser_id,
            "adgroup_id": adgroup_id,
            "count": len(ads),
            "ads": ads
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "error": True,
            "message": f"Error: {str(e)}",
            "suggestion": "Please check your configuration and try again."
        }, indent=2)

@app.tool()
def get_reports_tool(
    advertiser_id: Optional[str] = None,
    advertiser_ids: Optional[List[str]] = None,
    bc_id: Optional[str] = None,
    report_type: str = "BASIC",
    data_level: str = "AUCTION_CAMPAIGN",
    dimensions: Optional[List[str]] = None,
    metrics: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    filters: Optional[List[Dict]] = None,
    page: int = 1,
    page_size: int = 10,
    service_type: str = "AUCTION",
    query_lifetime: bool = False,
    enable_total_metrics: bool = False,
    multi_adv_report_in_utc_time: bool = False,
    order_field: Optional[str] = None,
    order_type: str = "DESC"
) -> str:
    """Get performance reports and analytics with comprehensive filtering and grouping options"""
    
    try:
        client = get_tiktok_client()
        reports = get_reports(
            client,
            advertiser_id=advertiser_id,
            advertiser_ids=advertiser_ids,
            bc_id=bc_id,
            report_type=report_type,
            data_level=data_level,
            dimensions=dimensions or ["campaign_id", "stat_time_day"],
            metrics=metrics or ["spend", "impressions"],
            start_date=start_date,
            end_date=end_date,
            filters=filters,
            page=page,
            page_size=page_size,
            service_type=service_type,
            query_lifetime=query_lifetime,
            enable_total_metrics=enable_total_metrics,
            multi_adv_report_in_utc_time=multi_adv_report_in_utc_time,
            order_field=order_field,
            order_type=order_type
        )
        
        return json.dumps({
            "success": True,
            "report_type": report_type,
            "data_level": data_level,
            "total_metrics": reports.get("total_metrics"),
            "page_info": reports.get("page_info", {}),
            "count": len(reports.get("list", [])),
            "reports": reports.get("list", [])
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "error": True,
            "message": f"Error: {str(e)}",
            "suggestion": "Please check your configuration and try again."
        }, indent=2)

def main():
    """Main function to run the MCP server"""
    logger.info("Starting TikTok Ads MCP Server...")
    
    # Log configuration status
    try:
        if not config.validate_credentials():
            logger.warning("Missing credentials detected. Server will start but API calls will fail.")
            missing = config.get_missing_credentials()
            logger.warning(f"Missing: {', '.join(missing)}")
        else:
            logger.info("Configuration validated successfully")
    except Exception as e:
        logger.error(f"Failed to check configuration: {e}")
    
    # Run the MCP server using stdio transport
    app.run(transport="stdio")

if __name__ == "__main__":
    main() 