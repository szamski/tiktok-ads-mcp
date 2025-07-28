#!/usr/bin/env python3
"""TikTok Ads MCP Server - Pure MCP Implementation

A pure MCP (Model Context Protocol) server for TikTok Business API integration.
Inspired by the meta-ads-mcp project architecture.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

# MCP imports
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio

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
app = Server("tiktok-ads")

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

def handle_error(func):
    """Decorator for consistent error handling across MCP tools"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            suggestion = "Please check your configuration and try again."
            logger.exception("Error in MCP tool")
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": True,
                    "error_type": "api",
                    "message": error_msg,
                    "suggestion": suggestion
                }, indent=2)
            )]
    return wrapper

@app.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available TikTok Ads tools with detailed descriptions"""
    return [
        types.Tool(
            name="get_business_centers",
            description="Get business centers accessible by the current access token",
            inputSchema={
                "type": "object",
                "properties": {
                    "bc_id": {
                        "type": "string",
                        "description": "Business Center ID (optional). When not passed, returns all Business Centers."
                    },
                    "page": {
                        "type": "integer",
                        "description": "Current page number",
                        "default": 1,
                        "minimum": 1
                    },
                    "page_size": {
                        "type": "integer", 
                        "description": "Page size (1-50)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    }
                }
            }
        ),
        types.Tool(
            name="get_authorized_ad_accounts",
            description="Get all authorized ad accounts accessible by the current access token",
            inputSchema={
                "type": "object",
                "properties": {
                    "random_string": {
                        "type": "string",
                        "description": "Dummy parameter for no-parameter tools",
                        "default": ""
                    }
                }
            }
        ),
        types.Tool(
            name="get_campaigns",
            description="Get campaigns for a specific advertiser with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "advertiser_id": {
                        "type": "string",
                        "description": "TikTok advertiser ID (required)"
                    },
                    "filters": {
                        "type": "object",
                        "description": "Optional filters (campaign_ids, etc.)",
                        "default": {}
                    }
                },
                "required": ["advertiser_id"]
            }
        ),
        types.Tool(
            name="get_ad_groups",
            description="Get ad groups for a specific advertiser with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "advertiser_id": {
                        "type": "string",
                        "description": "TikTok advertiser ID (required)"
                    },
                    "campaign_id": {
                        "type": "string",
                        "description": "Campaign ID to filter by (optional)"
                    },
                    "filters": {
                        "type": "object",
                        "description": "Optional filtering options",
                        "properties": {
                            "campaign_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of campaign IDs to filter by"
                            },
                            "adgroup_ids": {
                                "type": "array", 
                                "items": {"type": "string"},
                                "description": "List of ad group IDs to filter by"
                            },
                            "adgroup_name": {
                                "type": "string",
                                "description": "Ad group name to filter by"
                            },
                            "primary_status": {
                                "type": "string",
                                "description": "Primary status filter",
                                "enum": ["STATUS_NOT_DELETE", "STATUS_ALL"]
                            },
                            "secondary_status": {
                                "type": "string",
                                "description": "Secondary status filter"
                    },
                            "objective_type": {
                                "type": "string",
                                "description": "Advertising objective filter"
                            },
                            "optimization_goal": {
                                "type": "string",
                                "description": "Optimization goal filter"
                            },
                            "promotion_type": {
                                "type": "string",
                                "description": "Promotion type filter",
                                "enum": ["APP", "WEBSITE", "INSTANT_FORM", "LEAD_GEN_CLICK_TO_TT_DIRECT_MESSAGE", "LEAD_GEN_CLICK_TO_SOCIAL_MEDIA_APP_MESSAGE", "LEAD_GEN_CLICK_TO_CALL"]
                            },
                            "bid_strategy": {
                                "type": "string",
                                "description": "Bidding strategy filter",
                                "enum": ["BID_STRATEGY_COST_CAP", "BID_STRATEGY_BID_CAP", "BID_STRATEGY_MAX_CONVERSION", "BID_STRATEGY_LOWEST_COST"]
                            },
                            "creative_material_mode": {
                                "type": "string",
                                "description": "Creative material mode filter",
                                "enum": ["CUSTOM", "SMART_CREATIVE"]
                            },
                            "creation_filter_start_time": {
                        "type": "string",
                                "description": "Filter by creation start time (YYYY-MM-DD HH:MM:SS UTC)"
                    },
                            "creation_filter_end_time": {
                        "type": "string",
                                "description": "Filter by creation end time (YYYY-MM-DD HH:MM:SS UTC)"
                    },
                            "split_test_enabled": {
                                "type": "boolean",
                                "description": "Filter by split test enabled status"
                            }
                        }
                    },
                    "page": {
                        "type": "integer",
                        "description": "Current page number",
                        "default": 1,
                        "minimum": 1
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "Page size (1-1000)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 1000
                    }
                },
                "required": ["advertiser_id"]
            }
        ),
        types.Tool(
            name="get_ads",
            description="Get ads for a specific advertiser with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "advertiser_id": {
                        "type": "string",
                        "description": "TikTok advertiser ID (required)"
                    },
                    "adgroup_id": {
                        "type": "string",
                        "description": "Ad group ID to filter by (optional)"
                    },
                    "filters": {
                        "type": "object",
                        "description": "Optional filtering options",
                        "properties": {
                            "campaign_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of campaign IDs to filter by"
                            },
                            "adgroup_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of ad group IDs to filter by"
                            },
                            "ad_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of ad IDs to filter by"
                            },
                            "primary_status": {
                                "type": "string",
                                "description": "Primary status filter"
                            },
                            "secondary_status": {
                                "type": "string",
                                "description": "Secondary status filter"
                            },
                            "objective_type": {
                                "type": "string",
                                "description": "Advertising objective filter"
                            },
                            "buying_types": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Buying types filter",
                                "enum": ["AUCTION", "RESERVATION_RF", "RESERVATION_TOP_VIEW"]
                            },
                            "optimization_goal": {
                                "type": "string",
                                "description": "Optimization goal filter"
                            },
                            "creative_material_mode": {
                                "type": "string",
                                "description": "Creative material mode filter",
                                "enum": ["CUSTOM", "DYNAMIC", "SMART_CREATIVE"]
                            },
                            "destination": {
                                "type": "string",
                                "description": "Destination page type filter",
                                "enum": ["APP", "TIKTOK_INSTANT_PAGE", "WEBSITE", "SOCIAL_MEDIA_APP", "PHONE_CALL"]
                            },
                            "creation_filter_start_time": {
                                "type": "string",
                                "description": "Filter by creation start time (YYYY-MM-DD HH:MM:SS UTC)"
                            },
                            "creation_filter_end_time": {
                                "type": "string",
                                "description": "Filter by creation end time (YYYY-MM-DD HH:MM:SS UTC)"
                            },
                            "modified_after": {
                                "type": "string",
                                "description": "Filter by modification time (YYYY-MM-DD HH:MM:SS UTC)"
                            }
                        }
                    },
                    "page": {
                        "type": "integer",
                        "description": "Current page number",
                        "default": 1,
                        "minimum": 1
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "Page size (1-1000)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 1000
                    }
                },
                "required": ["advertiser_id"]
            }
        ),
        types.Tool(
            name="get_reports",
            description="Get performance reports and analytics with comprehensive filtering and grouping options",
            inputSchema={
                "type": "object",
                "properties": {
                    "advertiser_id": {
                        "type": "string",
                        "description": "TikTok advertiser ID (required for non-BC reports)"
                    },
                    "advertiser_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of advertiser IDs (max 5, for multi-advertiser reports)"
                    },
                    "bc_id": {
                        "type": "string",
                        "description": "Business Center ID (required for BC reports)"
                    },
                    "report_type": {
                        "type": "string",
                        "description": "Report type",
                        "enum": ["BASIC", "AUDIENCE", "PLAYABLE_MATERIAL", "CATALOG", "BC", "TT_SHOP"],
                        "default": "BASIC"
                    },
                    "data_level": {
                        "type": "string",
                        "description": "Data aggregation level (required for non-BC reports)",
                        "enum": ["AUCTION_AD", "AUCTION_ADGROUP", "AUCTION_CAMPAIGN", "AUCTION_ADVERTISER"],
                        "default": "AUCTION_CAMPAIGN"
                    },
                    "dimensions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Grouping conditions (e.g., ['campaign_id', 'stat_time_day'])",
                        "default": ["campaign_id", "stat_time_day"]
                    },
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Metrics to query (e.g., ['spend', 'impressions', 'clicks'])",
                        "default": ["spend", "impressions"]
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Query start date (YYYY-MM-DD, required when query_lifetime is false)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Query end date (YYYY-MM-DD, required when query_lifetime is false)"
                    },
                    "filters": {
                        "type": "array",
                        "description": "Filtering conditions",
                        "items": {
                            "type": "object",
                            "properties": {
                                "field_name": {"type": "string"},
                                "filter_type": {
                                    "type": "string",
                                    "enum": ["IN", "MATCH", "GREATER_EQUAL", "GREATER_THAN", "LOWER_EQUAL", "LOWER_THAN", "BETWEEN"]
                                },
                                "filter_value": {"type": "string"}
                }
            }
                    },
                    "service_type": {
                        "type": "string",
                        "description": "Ad service type",
                        "enum": ["AUCTION", "RESERVATION"],
                        "default": "AUCTION"
                    },
                    "query_lifetime": {
                        "type": "boolean",
                        "description": "Whether to request lifetime metrics",
                        "default": False
                    },
                    "enable_total_metrics": {
                        "type": "boolean",
                        "description": "Enable total added-up data for metrics",
                        "default": False
                    },
                    "multi_adv_report_in_utc_time": {
                        "type": "boolean",
                        "description": "Set returned metrics in UTC timezone for multi-advertiser reports",
                        "default": False
                    },
                    "order_field": {
                        "type": "string",
                        "description": "Sorting field"
                    },
                    "order_type": {
                        "type": "string",
                        "description": "Sorting order",
                        "enum": ["ASC", "DESC"],
                        "default": "DESC"
                    },
                    "page": {
                        "type": "integer",
                        "description": "Current page number",
                        "default": 1,
                        "minimum": 1
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "Page size (1-1000)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 1000
                    }
                }
            }
        ),

    ]

# Tool implementations

@handle_error
def get_business_centers_impl(bc_id: str = "", page: int = 1, page_size: int = 10) -> List[types.TextContent]:
    """Get business centers"""
    client = get_tiktok_client()
    centers = get_business_centers(client, bc_id=bc_id, page=page, page_size=page_size)
    
    return [types.TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "count": len(centers),
            "centers": centers
        }, indent=2)
    )]

@handle_error
def get_authorized_ad_accounts_impl(random_string: str = "") -> List[types.TextContent]:
    """Get all authorized ad accounts"""
    client = get_tiktok_client()
    advertisers = get_authorized_ad_accounts(client)
    
    return [types.TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "count": len(advertisers),
            "advertisers": advertisers
        }, indent=2)
    )]

@handle_error
def get_campaigns_impl(advertiser_id: str, filters: Dict = None) -> List[types.TextContent]:
    """Get campaigns for a specific advertiser"""
    if not advertiser_id:
        raise ValueError("advertiser_id is required")
    
    client = get_tiktok_client()
    campaigns = get_campaigns(client, advertiser_id=advertiser_id, filters=filters or {})
    
    return [types.TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "advertiser_id": advertiser_id,
            "count": len(campaigns),
            "campaigns": campaigns
        }, indent=2)
    )]

@handle_error
def get_ad_groups_impl(advertiser_id: str, campaign_id: str = None, filters: Dict = None, page: int = 1, page_size: int = 10) -> List[types.TextContent]:
    """Get ad groups for a specific advertiser"""
    if not advertiser_id:
        raise ValueError("advertiser_id is required")
    
    client = get_tiktok_client()
    ad_groups = get_ad_groups(client, advertiser_id=advertiser_id, campaign_id=campaign_id, filters=filters or {})
    
    return [types.TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "advertiser_id": advertiser_id,
            "campaign_id": campaign_id,
            "count": len(ad_groups),
            "ad_groups": ad_groups
        }, indent=2)
    )]

@handle_error
def get_ads_impl(advertiser_id: str, adgroup_id: str = None, filters: Dict = None, page: int = 1, page_size: int = 10) -> List[types.TextContent]:
    """Get ads for a specific advertiser"""
    if not advertiser_id:
        raise ValueError("advertiser_id is required")
    
    client = get_tiktok_client()
    ads = get_ads(client, advertiser_id=advertiser_id, adgroup_id=adgroup_id, filters=filters or {})
    return [types.TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "advertiser_id": advertiser_id,
            "adgroup_id": adgroup_id,
            "count": len(ads),
            "ads": ads
            }, indent=2)
        )]

@handle_error
def get_reports_impl(advertiser_id: str = None, advertiser_ids: List[str] = None, bc_id: str = None,
                     report_type: str = "BASIC", data_level: str = "AUCTION_CAMPAIGN",
                     dimensions: List[str] = None, metrics: List[str] = None,
                     start_date: str = None, end_date: str = None, filters: List[Dict] = None,
                     page: int = 1, page_size: int = 10, service_type: str = "AUCTION",
                     query_lifetime: bool = False, enable_total_metrics: bool = False,
                     multi_adv_report_in_utc_time: bool = False, order_field: str = None,
                     order_type: str = "DESC") -> List[types.TextContent]:
    """Get performance reports"""
    
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
    
    return [types.TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "report_type": report_type,
            "data_level": data_level,
            "total_metrics": reports.get("total_metrics"),
            "page_info": reports.get("page_info", {}),
            "count": len(reports.get("list", [])),
            "reports": reports.get("list", [])
        }, indent=2)
    )]





@app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls with enhanced error handling and validation"""
    
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    
    # Dispatch to appropriate function
    if name == "get_business_centers":
        bc_id = arguments.get("bc_id", "")
        page = arguments.get("page", 1)
        page_size = arguments.get("page_size", 10)
        return get_business_centers_impl(bc_id=bc_id, page=page, page_size=page_size)
        
    elif name == "get_authorized_ad_accounts":
        random_string = arguments.get("random_string", "")
        return get_authorized_ad_accounts_impl(random_string=random_string)
        
    elif name == "get_campaigns":
        advertiser_id = arguments.get("advertiser_id")
        filters = arguments.get("filters", {})
        return get_campaigns_impl(advertiser_id=advertiser_id, filters=filters)
        
    elif name == "get_ad_groups":
        advertiser_id = arguments.get("advertiser_id")
        campaign_id = arguments.get("campaign_id")
        filters = arguments.get("filters", {})
        page = arguments.get("page", 1)
        page_size = arguments.get("page_size", 10)
        return get_ad_groups_impl(advertiser_id=advertiser_id, campaign_id=campaign_id, filters=filters, page=page, page_size=page_size)
        
    elif name == "get_ads":
        advertiser_id = arguments.get("advertiser_id")
        adgroup_id = arguments.get("adgroup_id")
        filters = arguments.get("filters", {})
        page = arguments.get("page", 1)
        page_size = arguments.get("page_size", 10)
        return get_ads_impl(advertiser_id=advertiser_id, adgroup_id=adgroup_id, filters=filters, page=page, page_size=page_size)
        
    elif name == "get_reports":
        advertiser_id = arguments.get("advertiser_id")
        advertiser_ids = arguments.get("advertiser_ids", [])
        bc_id = arguments.get("bc_id")
        report_type = arguments.get("report_type", "BASIC")
        data_level = arguments.get("data_level", "AUCTION_CAMPAIGN")
        dimensions = arguments.get("dimensions", ["campaign_id", "stat_time_day"])
        metrics = arguments.get("metrics", ["spend", "impressions"])
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date")
        filters = arguments.get("filters", [])
        page = arguments.get("page", 1)
        page_size = arguments.get("page_size", 10)
        service_type = arguments.get("service_type", "AUCTION")
        query_lifetime = arguments.get("query_lifetime", False)
        enable_total_metrics = arguments.get("enable_total_metrics", False)
        multi_adv_report_in_utc_time = arguments.get("multi_adv_report_in_utc_time", False)
        order_field = arguments.get("order_field")
        order_type = arguments.get("order_type", "DESC")
        
        return get_reports_impl(
            advertiser_id=advertiser_id,
            advertiser_ids=advertiser_ids,
            bc_id=bc_id,
            report_type=report_type,
            data_level=data_level,
            dimensions=dimensions,
            metrics=metrics,
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
        

    
    else:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": True,
                "message": f"Unknown tool: {name}",
                "available_tools": ["get_business_centers", "get_authorized_ad_accounts", "get_campaigns", "get_ad_groups", "get_ads", "get_reports"]
            }, indent=2)
        )]

async def main():
    """Main function to run the pure MCP server"""
    logger.info("Starting TikTok Ads MCP Server (Pure MCP Architecture)...")
    
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
    
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="tiktok-ads",
                server_version="2.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 