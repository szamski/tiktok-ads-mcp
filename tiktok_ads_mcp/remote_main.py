#!/usr/bin/env python3
"""Remote MCP Server Entry Point for TikTok Ads

Entry point for running the TikTok Ads MCP server as a remote Claude Connector.
Supports both development and production deployment configurations.
"""

import argparse
import logging
import os
import sys
from typing import Optional

import uvicorn
from dotenv import load_dotenv

from .config import config
from .remote_server import app

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_environment() -> bool:
    """Validate required environment variables and configuration"""
    try:
        # Check TikTok API credentials
        missing_credentials = config.get_missing_credentials()
        if missing_credentials:
            logger.error("Missing required TikTok API credentials:")
            for cred in missing_credentials:
                logger.error(f"  - {cred}")
            logger.error("Please set the required environment variables.")
            return False
        
        logger.info("TikTok API credentials validated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Environment validation failed: {e}")
        return False

def get_server_config() -> dict:
    """Get server configuration from environment variables"""
    return {
        "host": os.getenv("HOST", "0.0.0.0"),
        "port": int(os.getenv("PORT", "8000")),
        "workers": int(os.getenv("WORKERS", "1")),
        "reload": os.getenv("RELOAD", "false").lower() == "true",
        "log_level": os.getenv("LOG_LEVEL", "info").lower(),
        "access_log": os.getenv("ACCESS_LOG", "true").lower() == "true",
    }

def run_server(
    host: Optional[str] = None,
    port: Optional[int] = None,
    workers: Optional[int] = None,
    reload: Optional[bool] = None,
    log_level: Optional[str] = None,
    validate_env: bool = True
):
    """Run the remote MCP server"""
    try:
        # Validate environment if requested
        if validate_env and not validate_environment():
            logger.error("Environment validation failed. Server will not start.")
            sys.exit(1)
        
        # Get server configuration
        server_config = get_server_config()
        
        # Override with provided parameters
        if host is not None:
            server_config["host"] = host
        if port is not None:
            server_config["port"] = port
        if workers is not None:
            server_config["workers"] = workers
        if reload is not None:
            server_config["reload"] = reload
        if log_level is not None:
            server_config["log_level"] = log_level
        
        # Log startup information
        logger.info("=" * 60)
        logger.info("TikTok Ads MCP Remote Server")
        logger.info("=" * 60)
        logger.info(f"Host: {server_config['host']}")
        logger.info(f"Port: {server_config['port']}")
        logger.info(f"Workers: {server_config['workers']}")
        logger.info(f"Reload: {server_config['reload']}")
        logger.info(f"Log Level: {server_config['log_level']}")
        logger.info("=" * 60)
        logger.info("Server starting...")
        
        # Start the server
        uvicorn.run(
            "tiktok_ads_mcp.remote_server:app",
            host=server_config["host"],
            port=server_config["port"],
            workers=server_config["workers"] if not server_config["reload"] else 1,
            reload=server_config["reload"],
            log_level=server_config["log_level"],
            access_log=server_config["access_log"],
            server_header=False,
            date_header=False
        )
        
    except KeyboardInterrupt:
        logger.info("Server shutdown by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)

def cli():
    """Command-line interface for the remote MCP server"""
    parser = argparse.ArgumentParser(
        description="TikTok Ads MCP Remote Server - Claude Connector"
    )
    
    parser.add_argument(
        "--host",
        default=None,
        help="Host address to bind to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to listen on (default: 8000)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of worker processes (default: 1)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        default=None,
        help="Log level (default: info)"
    )
    
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip environment validation on startup"
    )
    
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Development mode (enables reload and debug logging)"
    )
    
    args = parser.parse_args()
    
    # Handle development mode
    if args.dev:
        args.reload = True
        if not args.log_level:
            args.log_level = "debug"
        logger.info("Development mode enabled")
    
    # Run the server
    run_server(
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload,
        log_level=args.log_level,
        validate_env=not args.no_validate
    )

if __name__ == "__main__":
    cli()