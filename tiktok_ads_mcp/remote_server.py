#!/usr/bin/env python3
"""Remote MCP Server for TikTok Ads

A FastAPI-based remote MCP server implementation that provides Claude Connector compatibility.
Supports both HTTP and SSE transports with OAuth 2.0 authentication and Dynamic Client Registration.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

import httpx
from authlib.integrations.base_client import OAuthError
from authlib.oauth2 import OAuth2Error
from authlib.oauth2.client import OAuth2Client
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from uvicorn import run

from .client import TikTokAdsClient
from .config import config
from .tools import (
    get_ads,
    get_ad_groups,
    get_authorized_ad_accounts,
    get_business_centers,
    get_campaigns,
    get_reports,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="TikTok Ads MCP Remote Server",
    description="Remote MCP server for TikTok Business API integration with Claude Connector support",
    version="0.2.0",
)

# CORS middleware - Allow Render domain and Claude domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://claude.ai", 
        "https://claude.com",
        "*"  # Allow all origins for development - restrict in production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Global client instance
tiktok_client: Optional[TikTokAdsClient] = None

# OAuth configuration
OAUTH_CONFIG = {
    "client_name": "Claude",
    "client_uri": "https://claude.ai",
    "redirect_uris": [
        "https://claude.ai/api/mcp/auth_callback",
        "https://claude.com/api/mcp/auth_callback"
    ],
    "grant_types": ["authorization_code", "refresh_token"],
    "response_types": ["code"],
    "token_endpoint_auth_method": "client_secret_basic",
    "scope": "read",
}

# Pydantic models for MCP protocol
class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int]
    method: str
    params: Optional[Dict[str, Any]] = None

class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int]
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

class MCPTool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]

class MCPToolResult(BaseModel):
    content: List[Dict[str, Any]]
    isError: bool = False

# Tool definitions for MCP protocol
MCP_TOOLS = [
    MCPTool(
        name="get_business_centers",
        description="Get business centers accessible by the current access token",
        inputSchema={
            "type": "object",
            "properties": {
                "bc_id": {"type": "string", "description": "Specific business center ID (optional)"},
                "page": {"type": "integer", "default": 1, "description": "Page number"},
                "page_size": {"type": "integer", "default": 10, "description": "Items per page"}
            }
        }
    ),
    MCPTool(
        name="get_authorized_ad_accounts",
        description="Get all authorized ad accounts accessible by the current access token",
        inputSchema={
            "type": "object",
            "properties": {
                "random_string": {"type": "string", "description": "Optional parameter"}
            }
        }
    ),
    MCPTool(
        name="get_campaigns",
        description="Get campaigns for a specific advertiser with optional filtering",
        inputSchema={
            "type": "object",
            "properties": {
                "advertiser_id": {"type": "string", "description": "Advertiser ID (required)"},
                "filters": {"type": "object", "description": "Optional filtering parameters"}
            },
            "required": ["advertiser_id"]
        }
    ),
    MCPTool(
        name="get_ad_groups",
        description="Get ad groups for a specific advertiser with optional filtering",
        inputSchema={
            "type": "object",
            "properties": {
                "advertiser_id": {"type": "string", "description": "Advertiser ID (required)"},
                "campaign_id": {"type": "string", "description": "Campaign ID (optional)"},
                "filters": {"type": "object", "description": "Optional filtering parameters"},
                "page": {"type": "integer", "default": 1, "description": "Page number"},
                "page_size": {"type": "integer", "default": 10, "description": "Items per page"}
            },
            "required": ["advertiser_id"]
        }
    ),
    MCPTool(
        name="get_ads",
        description="Get ads for a specific advertiser with optional filtering",
        inputSchema={
            "type": "object",
            "properties": {
                "advertiser_id": {"type": "string", "description": "Advertiser ID (required)"},
                "adgroup_id": {"type": "string", "description": "Ad group ID (optional)"},
                "filters": {"type": "object", "description": "Optional filtering parameters"},
                "page": {"type": "integer", "default": 1, "description": "Page number"},
                "page_size": {"type": "integer", "default": 10, "description": "Items per page"}
            },
            "required": ["advertiser_id"]
        }
    ),
    MCPTool(
        name="get_reports",
        description="Get performance reports and analytics with comprehensive filtering and grouping options",
        inputSchema={
            "type": "object",
            "properties": {
                "advertiser_id": {"type": "string", "description": "Single advertiser ID"},
                "advertiser_ids": {"type": "array", "items": {"type": "string"}, "description": "Multiple advertiser IDs"},
                "bc_id": {"type": "string", "description": "Business center ID"},
                "report_type": {"type": "string", "default": "BASIC", "description": "Report type"},
                "data_level": {"type": "string", "default": "AUCTION_CAMPAIGN", "description": "Data aggregation level"},
                "dimensions": {"type": "array", "items": {"type": "string"}, "description": "Report dimensions"},
                "metrics": {"type": "array", "items": {"type": "string"}, "description": "Metrics to include"},
                "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                "filters": {"type": "array", "description": "Filter conditions"},
                "page": {"type": "integer", "default": 1, "description": "Page number"},
                "page_size": {"type": "integer", "default": 10, "description": "Items per page"}
            }
        }
    ),
]

def get_tiktok_client() -> TikTokAdsClient:
    """Get or create TikTok API client instance"""
    global tiktok_client
    
    if tiktok_client is None:
        try:
            tiktok_client = TikTokAdsClient()
            logger.info("TikTok API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TikTok client: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize TikTok client: {e}"
            )
    
    return tiktok_client

# MCP Protocol Endpoints

@app.get("/.well-known/mcp_server")
async def mcp_server_info(request: Request):
    """MCP server discovery endpoint"""
    base_url = str(request.url).replace(str(request.url.path), "").rstrip('/')
    
    return {
        "protocolVersion": "2024-11-05",
        "implementation": {
            "name": "tiktok-ads-mcp",
            "version": "0.2.0"
        },
        "serverInfo": {
            "name": "tiktok-ads-mcp", 
            "version": "0.2.0",
            "description": "Remote MCP server for TikTok Business API integration",
            "author": "TikTok Ads MCP Team",
            "homepage": "https://github.com/szamski/tiktok-ads-mcp"
        },
        "capabilities": {
            "tools": {
                "listChanged": True
            },
            "logging": {}
        },
        "transport": {
            "type": "http",
            "base_url": base_url,
            "endpoints": {
                "jsonrpc": "/"
            }
        },
        "authentication": {
            "type": "oauth2",
            "flows": {
                "authorization_code": {
                    "authorization_url": f"{base_url}/authorize",
                    "token_url": f"{base_url}/oauth/token"
                }
            },
            "registration_url": f"{base_url}/oauth/register"
        }
    }

@app.post("/mcp")
async def handle_mcp_request(request: MCPRequest):
    """Main MCP protocol handler"""
    try:
        if request.method == "initialize":
            return MCPResponse(
                id=request.id,
                result={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {
                            "listChanged": True
                        },
                        "logging": {}
                    },
                    "serverInfo": {
                        "name": "tiktok-ads-mcp",
                        "version": "0.2.0",
                        "description": "Remote MCP server for TikTok Business API integration"
                    },
                    "implementation": {
                        "name": "tiktok-ads-mcp-remote-server",
                        "version": "0.2.0"
                    }
                }
            )
        
        elif request.method == "tools/list":
            return MCPResponse(
                id=request.id,
                result={
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description, 
                            "inputSchema": tool.inputSchema
                        } for tool in MCP_TOOLS
                    ]
                }
            )
        
        elif request.method == "tools/call":
            return await handle_tool_call(request)
        
        else:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32601,
                    "message": f"Method not found: {request.method}"
                }
            )
    
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}")
        return MCPResponse(
            id=request.id,
            error={
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        )

# Individual MCP endpoints for direct access
@app.get("/mcp/tools/list")
async def list_tools():
    """List available tools endpoint"""
    return {
        "jsonrpc": "2.0",
        "result": {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                } for tool in MCP_TOOLS
            ]
        }
    }

@app.post("/mcp/tools/call")
async def call_tool(request: MCPRequest):
    """Call tool endpoint"""
    return await handle_tool_call(request)

@app.post("/mcp/tools/list")
async def list_tools_post(request: MCPRequest):
    """List tools via POST"""
    return MCPResponse(
        id=request.id,
        result={
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                } for tool in MCP_TOOLS
            ]
        }
    )

async def handle_tool_call(request: MCPRequest) -> MCPResponse:
    """Handle MCP tool call requests"""
    params = request.params or {}
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    try:
        # Check if TikTok credentials are configured
        from .config import config
        if not config.validate_credentials():
            missing = config.get_missing_credentials()
            return MCPResponse(
                id=request.id,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({
                                "error": True,
                                "tool": tool_name,
                                "message": f"TikTok API credentials not configured. Missing: {', '.join(missing)}",
                                "suggestion": "Please set the required environment variables: TIKTOK_APP_ID, TIKTOK_SECRET, TIKTOK_ACCESS_TOKEN"
                            }, indent=2)
                        }
                    ],
                    "isError": True
                }
            )
        
        client = get_tiktok_client()
        
        if tool_name == "get_business_centers":
            result = get_business_centers(
                client, 
                bc_id=arguments.get("bc_id", ""),
                page=arguments.get("page", 1),
                page_size=arguments.get("page_size", 10)
            )
            
        elif tool_name == "get_authorized_ad_accounts":
            result = get_authorized_ad_accounts(client)
            
        elif tool_name == "get_campaigns":
            if not arguments.get("advertiser_id"):
                raise ValueError("advertiser_id is required")
            result = get_campaigns(
                client,
                advertiser_id=arguments["advertiser_id"],
                filters=arguments.get("filters", {})
            )
            
        elif tool_name == "get_ad_groups":
            if not arguments.get("advertiser_id"):
                raise ValueError("advertiser_id is required")
            result = get_ad_groups(
                client,
                advertiser_id=arguments["advertiser_id"],
                campaign_id=arguments.get("campaign_id"),
                filters=arguments.get("filters", {})
            )
            
        elif tool_name == "get_ads":
            if not arguments.get("advertiser_id"):
                raise ValueError("advertiser_id is required")
            result = get_ads(
                client,
                advertiser_id=arguments["advertiser_id"],
                adgroup_id=arguments.get("adgroup_id"),
                filters=arguments.get("filters", {})
            )
            
        elif tool_name == "get_reports":
            result = get_reports(
                client,
                advertiser_id=arguments.get("advertiser_id"),
                advertiser_ids=arguments.get("advertiser_ids"),
                bc_id=arguments.get("bc_id"),
                report_type=arguments.get("report_type", "BASIC"),
                data_level=arguments.get("data_level", "AUCTION_CAMPAIGN"),
                dimensions=arguments.get("dimensions", ["campaign_id", "stat_time_day"]),
                metrics=arguments.get("metrics", ["spend", "impressions"]),
                start_date=arguments.get("start_date"),
                end_date=arguments.get("end_date"),
                filters=arguments.get("filters"),
                page=arguments.get("page", 1),
                page_size=arguments.get("page_size", 10)
            )
            
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        # Format result for MCP protocol
        formatted_result = {
            "success": True,
            "tool": tool_name,
            "data": result
        }
        
        return MCPResponse(
            id=request.id,
            result={
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(formatted_result, indent=2)
                    }
                ]
            }
        )
    
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        return MCPResponse(
            id=request.id,
            result={
                "content": [
                    {
                        "type": "text", 
                        "text": json.dumps({
                            "error": True,
                            "tool": tool_name,
                            "message": str(e),
                            "suggestion": "Please check your configuration and try again."
                        }, indent=2)
                    }
                ],
                "isError": True
            }
        )

# OAuth 2.0 Well-known endpoints
@app.get("/.well-known/oauth-authorization-server")
async def oauth_authorization_server():
    """OAuth 2.0 Authorization Server Metadata (RFC 8414)"""
    base_url = "https://tiktok-ads-mcp.onrender.com"  # Update with your actual domain
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/oauth/token",
        "registration_endpoint": f"{base_url}/oauth/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic"],
        "scopes_supported": ["read"],
        "code_challenge_methods_supported": ["S256"]
    }

@app.get("/.well-known/oauth-protected-resource")
async def oauth_protected_resource():
    """OAuth 2.0 Protected Resource Metadata (RFC 8705)"""
    base_url = "https://tiktok-ads-mcp.onrender.com"  # Update with your actual domain
    return {
        "resource": base_url,
        "authorization_servers": [base_url],
        "scopes_supported": ["read"],
        "bearer_methods_supported": ["header"]
    }

# OAuth 2.0 and Dynamic Client Registration endpoints

@app.post("/oauth/register")
async def register_oauth_client(request: Request):
    """Dynamic Client Registration endpoint (RFC 7591)"""
    try:
        body = await request.json()
        
        # Validate required fields
        required_fields = ["redirect_uris", "client_name"]
        for field in required_fields:
            if field not in body:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Validate redirect URIs for Claude
        valid_uris = [
            "https://claude.ai/api/mcp/auth_callback",
            "https://claude.com/api/mcp/auth_callback"
        ]
        
        if not any(uri in body["redirect_uris"] for uri in valid_uris):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid redirect URI. Must use Claude callback URL."
            )
        
        # Generate client credentials
        import secrets
        client_id = f"tiktok-ads-mcp-{secrets.token_urlsafe(16)}"
        client_secret = secrets.token_urlsafe(32)
        
        # Store client registration (in production, use a proper database)
        registration_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_name": body.get("client_name", "Claude"),
            "redirect_uris": body["redirect_uris"],
            "grant_types": body.get("grant_types", ["authorization_code", "refresh_token"]),
            "response_types": body.get("response_types", ["code"]),
            "scope": body.get("scope", "read"),
            "created_at": datetime.utcnow().isoformat()
        }
        
        # In production, store this in a database
        # For now, we'll use environment variables or in-memory storage
        
        logger.info(f"Registered OAuth client: {client_id}")
        
        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_name": registration_data["client_name"],
            "redirect_uris": registration_data["redirect_uris"],
            "grant_types": registration_data["grant_types"],
            "response_types": registration_data["response_types"],
            "token_endpoint_auth_method": "client_secret_basic",
            "scope": registration_data["scope"],
            "client_id_issued_at": int(datetime.utcnow().timestamp()),
            "client_secret_expires_at": 0  # Never expires
        }
    
    except Exception as e:
        logger.error(f"OAuth client registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Client registration failed: {str(e)}"
        )

@app.get("/authorize")
async def oauth_authorize(
    client_id: str,
    redirect_uri: str,
    response_type: str = "code",
    scope: str = "read",
    state: Optional[str] = None,
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = None,
    resource: Optional[str] = None
):
    """OAuth 2.0 authorization endpoint with PKCE support"""
    try:
        # Validate client_id and redirect_uri
        # In production, validate against stored client registrations
        
        # Validate PKCE parameters
        if code_challenge and code_challenge_method != "S256":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported code_challenge_method. Only S256 is supported."
            )
        
        # Generate authorization code
        import secrets
        auth_code = secrets.token_urlsafe(32)
        
        # Store authorization code temporarily with PKCE info (use database in production)
        # In a real implementation, store: auth_code, code_challenge, client_id, etc.
        auth_storage = {
            auth_code: {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "code_challenge": code_challenge,
                "code_challenge_method": code_challenge_method,
                "scope": scope
            }
        }
        
        # Build callback URL
        params = {
            "code": auth_code,
        }
        if state:
            params["state"] = state
        
        callback_url = f"{redirect_uri}?{urlencode(params)}"
        
        # In a real implementation, this would redirect to a login page first
        # For this demo, we'll redirect directly with the code
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=callback_url, status_code=302)
    
    except Exception as e:
        logger.error(f"OAuth authorization error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authorization failed: {str(e)}"
        )

@app.post("/oauth/token")
async def oauth_token(request: Request):
    """OAuth 2.0 token endpoint"""
    try:
        # Handle both form data and JSON
        content_type = request.headers.get("content-type", "")
        
        if "application/x-www-form-urlencoded" in content_type:
            form_data = await request.form()
            data = dict(form_data)
        else:
            data = await request.json()
        
        grant_type = data.get("grant_type")
        
        if grant_type == "authorization_code":
            # Exchange authorization code for access token
            code = data.get("code")
            client_id = data.get("client_id")
            client_secret = data.get("client_secret")
            
            # Validate authorization code and client credentials
            # In production, verify against stored data
            
            # Generate tokens
            import secrets
            access_token = secrets.token_urlsafe(32)
            refresh_token = secrets.token_urlsafe(32)
            
            return {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": 3600,  # 1 hour
                "refresh_token": refresh_token,
                "scope": "read"
            }
        
        elif grant_type == "refresh_token":
            # Handle token refresh
            refresh_token = data.get("refresh_token")
            
            # Validate refresh token
            # Generate new access token
            import secrets
            new_access_token = secrets.token_urlsafe(32)
            
            return {
                "access_token": new_access_token,
                "token_type": "Bearer", 
                "expires_in": 3600,
                "scope": "read"
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported grant type: {grant_type}"
            )
    
    except Exception as e:
        logger.error(f"OAuth token error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token request failed: {str(e)}"
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test TikTok API connection
        client = get_tiktok_client()
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "tiktok-ads-mcp",
            "version": "0.2.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with server information"""
    return {
        "name": "TikTok Ads MCP Remote Server",
        "version": "0.2.0",
        "description": "Remote MCP server for TikTok Business API integration with Claude Connector support",
        "endpoints": {
            "mcp_discovery": "/.well-known/mcp_server",
            "mcp_protocol": "/mcp",
            "oauth_register": "/oauth/register",
            "oauth_authorize": "/authorize", 
            "oauth_token": "/oauth/token",
            "health": "/health"
        },
        "documentation": "/docs"
    }

@app.post("/")
async def root_post(request: Request):
    """Handle POST requests to root - redirect to MCP protocol handler"""
    try:
        # Check if this is an MCP request
        body = await request.json()
        if body.get("jsonrpc") == "2.0":
            # This is an MCP request, handle it
            mcp_request = MCPRequest(**body)
            return await handle_mcp_request(mcp_request)
        else:
            # Not an MCP request, return server info
            return await root()
    except Exception as e:
        # If JSON parsing fails, return server info
        return await root()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting TikTok Ads MCP Remote Server on {host}:{port}")
    run(app, host=host, port=port, log_level="info")