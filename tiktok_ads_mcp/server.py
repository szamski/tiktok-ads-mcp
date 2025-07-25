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

# TikTok client with enhanced authentication
from .client import TikTokAdsClient, TikTokAuthenticationError, TikTokAPIError
from .config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global client instance (will be initialized on first use)
tiktok_client: Optional[TikTokAdsClient] = None

# Create MCP server instance
app = Server("tiktok-ads")

def get_tiktok_client() -> TikTokAdsClient:
    """Get or create TikTok API client instance with proper error handling"""
    global tiktok_client
    
    if tiktok_client is None:
        try:
            tiktok_client = TikTokAdsClient()
            logger.info("TikTok API client initialized successfully")
        except TikTokAuthenticationError as e:
            logger.error(f"Authentication error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize TikTok client: {e}")
            raise TikTokAPIError(f"Client initialization failed: {str(e)}")
    
    return tiktok_client

def handle_error(func):
    """Decorator for consistent error handling across MCP tools"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TikTokAuthenticationError as e:
            error_msg = f"Authentication Error: {str(e)}"
            suggestion = "Please check your TIKTOK_ACCESS_TOKEN, TIKTOK_APP_ID, and TIKTOK_SECRET in your .env file."
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": True,
                    "error_type": "authentication",
                    "message": error_msg,
                    "suggestion": suggestion
                }, indent=2)
            )]
        except TikTokAPIError as e:
            error_msg = f"API Error: {str(e)}"
            suggestion = "This may be a temporary issue. Please try again in a few moments."
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": True,
                    "error_type": "api",
                    "message": error_msg,
                    "suggestion": suggestion
                }, indent=2)
            )]
        except Exception as e:
            error_msg = f"Unexpected Error: {str(e)}"
            suggestion = "Please check your configuration and try again."
            logger.exception("Unexpected error in MCP tool")
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": True,
                    "error_type": "unexpected",
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
            name="get_advertisers",
            description="Get all advertiser accounts accessible by the current access token. No parameters required.",
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
                        "description": "Optional filters (campaign_ids, status, etc.)",
                        "default": {}
                    }
                },
                "required": ["advertiser_id"]
            }
        ),
        types.Tool(
            name="get_insights",
            description="Get performance insights and metrics for campaigns, ad groups, or ads",
            inputSchema={
                "type": "object",
                "properties": {
                    "advertiser_id": {
                        "type": "string",
                        "description": "TikTok advertiser ID (required)"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format (required)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format (required)"
                    },
                    "data_level": {
                        "type": "string",
                        "description": "Data aggregation level",
                        "enum": ["AUCTION_CAMPAIGN", "AUCTION_ADGROUP", "AUCTION_AD"],
                        "default": "AUCTION_CAMPAIGN"
                    },
                    "metrics": {
                        "type": "array",
                        "description": "Metrics to retrieve",
                        "items": {"type": "string"},
                        "default": ["spend", "impressions", "clicks", "ctr", "cpm", "cpc"]
                    },
                    "object_ids": {
                        "type": "array",
                        "description": "Optional: Specific campaign, ad group, or ad IDs to get insights for",
                        "items": {"type": "string"},
                        "default": []
                    }
                },
                "required": ["advertiser_id", "start_date", "end_date"]
            }
        ),
        types.Tool(
            name="health_check",
            description="Check TikTok Business API health and connectivity",
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
            name="validate_token",
            description="Validate TikTok API access token and return detailed information about accessible accounts",
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
            name="get_auth_info",
            description="Get comprehensive authentication and configuration status information",
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
        )
    ]

# Tool implementations

@handle_error
def get_advertisers_impl(random_string: str = "") -> List[types.TextContent]:
    """Get all advertiser accounts"""
    client = get_tiktok_client()
    advertisers = client.get_advertisers()
    
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
    campaigns = client.get_campaigns(advertiser_id, filters or {})
    
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
def get_insights_impl(advertiser_id: str, start_date: str, end_date: str,
                     data_level: str = "AUCTION_CAMPAIGN", 
                     metrics: List[str] = None, 
                     object_ids: List[str] = None) -> List[types.TextContent]:
    """Get performance insights"""
    if not all([advertiser_id, start_date, end_date]):
        raise ValueError("advertiser_id, start_date, and end_date are required")
    
    client = get_tiktok_client()
    insights = client.get_insights(
        advertiser_id=advertiser_id,
        start_date=start_date,
        end_date=end_date,
        data_level=data_level,
        metrics=metrics,
        object_ids=object_ids
    )
    
    return [types.TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "advertiser_id": advertiser_id,
            "date_range": f"{start_date} to {end_date}",
            "data_level": data_level,
            "metrics": metrics or ["spend", "impressions", "clicks", "ctr", "cpm", "cpc"],
            "count": len(insights),
            "insights": insights
        }, indent=2)
    )]

@handle_error
def health_check_impl(random_string: str = "") -> List[types.TextContent]:
    """Check API health and connectivity"""
    try:
        client = get_tiktok_client()
        is_healthy = client.health_check()
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "healthy": is_healthy,
                "message": "API is accessible" if is_healthy else "API connection failed",
                "timestamp": json.dumps({"timestamp": "now"}, default=str)
            }, indent=2)
        )]
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "healthy": False,
                "message": f"Health check failed: {str(e)}"
            }, indent=2)
        )]

@handle_error
def validate_token_impl(random_string: str = "") -> List[types.TextContent]:
    """Validate access token and return detailed information"""
    client = get_tiktok_client()
    validation_result = client.validate_token()
    
    return [types.TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "validation": validation_result
        }, indent=2)
    )]

@handle_error
def get_auth_info_impl(random_string: str = "") -> List[types.TextContent]:
    """Get authentication and configuration status"""
    auth_info = config.get_auth_info()
    health_info = config.get_health_info()
    
    combined_info = {
        "success": True,
        "authentication": auth_info,
        "system_health": health_info,
        "server_version": "2.0.0"
    }
    
    return [types.TextContent(
        type="text",
        text=json.dumps(combined_info, indent=2)
    )]

@app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls with enhanced error handling and validation"""
    
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    
    # Dispatch to appropriate function
    if name == "get_advertisers":
        random_string = arguments.get("random_string", "")
        return get_advertisers_impl(random_string=random_string)
        
    elif name == "get_campaigns":
        advertiser_id = arguments.get("advertiser_id")
        filters = arguments.get("filters", {})
        return get_campaigns_impl(advertiser_id=advertiser_id, filters=filters)
        
    elif name == "get_insights":
        advertiser_id = arguments.get("advertiser_id")
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date")
        data_level = arguments.get("data_level", "AUCTION_CAMPAIGN")
        metrics = arguments.get("metrics", ["spend", "impressions", "clicks", "ctr", "cpm", "cpc"])
        object_ids = arguments.get("object_ids", [])
        
        return get_insights_impl(
            advertiser_id=advertiser_id,
            start_date=start_date,
            end_date=end_date,
            data_level=data_level,
            metrics=metrics,
            object_ids=object_ids
        )
        
    elif name == "health_check":
        random_string = arguments.get("random_string", "")
        return health_check_impl(random_string=random_string)
        
    elif name == "validate_token":
        random_string = arguments.get("random_string", "")
        return validate_token_impl(random_string=random_string)
        
    elif name == "get_auth_info":
        random_string = arguments.get("random_string", "")
        return get_auth_info_impl(random_string=random_string)
    
    else:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": True,
                "message": f"Unknown tool: {name}",
                "available_tools": ["get_advertisers", "get_campaigns", "get_insights", "health_check", "validate_token", "get_auth_info"]
            }, indent=2)
        )]

async def main():
    """Main function to run the pure MCP server"""
    logger.info("Starting TikTok Ads MCP Server (Pure MCP Architecture)...")
    
    # Log configuration status
    try:
        auth_info = config.get_auth_info()
        logger.info(f"Configuration status: {auth_info}")
        
        if not auth_info.get("has_credentials"):
            logger.warning("Missing credentials detected. Server will start but API calls will fail.")
            missing = auth_info.get("missing_credentials", [])
            logger.warning(f"Missing: {', '.join(missing)}")
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