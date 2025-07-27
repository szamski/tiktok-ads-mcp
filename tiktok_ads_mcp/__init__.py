"""TikTok Ads MCP - Python Package

A pure MCP (Model Context Protocol) server for TikTok Business API integration.
"""

__version__ = "0.1.1"
__author__ = "TikTok Ads MCP Team"

from .server import app, main
from .client import TikTokAdsClient
from .config import config

__all__ = ["app", "main", "TikTokAdsClient", "config"] 