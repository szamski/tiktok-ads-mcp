#!/usr/bin/env python3
"""Basic usage example for TikTok Ads MCP Server

This example shows how to run the TikTok Ads MCP server directly from the source,
without needing to install the package first. This is useful for development and testing.
"""

import asyncio
import sys
import os

# --- Development-only path modification ---
# This line allows the script to find the 'tiktok_ads_mcp' package in the parent directory.
# It's a standard pattern for running examples within a project structure.
# This is NOT needed when the package is installed via pip.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# -----------------------------------------

from tiktok_ads_mcp.server import main

if __name__ == "__main__":
    print("🚀 Starting TikTok Ads MCP Server from example script...")
    print("📖 For production, install the package and use the 'tiktok-ads-mcp' command.")
    print("⚠️  Make sure your .env file is configured in the project root.")
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)