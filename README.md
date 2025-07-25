# TikTok Ads MCP

[![PyPI version](https://badge.fury.io/py/tiktok-ads-mcp.svg)](https://badge.fury.io/py/tiktok-ads-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A **pure MCP (Model Context Protocol)** server for TikTok Business API integration, designed for AI-first interactions. Inspired by the [meta-ads-mcp](https://github.com/pipeboard-co/meta-ads-mcp.git) project architecture.

## 🎯 **Pure MCP Architecture**

This project follows the **pure MCP server design philosophy**:
- **AI-First**: Designed specifically for AI model consumption
- **Single Interface**: MCP protocol only - no extra CLI, web UI, or other human interfaces
- **Lightweight**: Minimal dependencies defined in `pyproject.toml` for core functionality
- **Production-Ready**: Enterprise-grade reliability and error handling

## 🚀 **Key Features**

### 🔐 **Enhanced Authentication System**
- **Robust Local Authentication** - Secure `.env`-based credential management
- **Token Validation** - Comprehensive API credential validation on startup
- **Smart Caching** - Performance-optimized response caching
- **Rate Limiting** - Built-in API rate limiting protection

### 🛡️ **Production-Ready Error Handling**
- **Custom Exception Types** - `TikTokAuthenticationError` and `TikTokAPIError`
- **Detailed Error Messages** - Clear error descriptions with actionable suggestions
- **Graceful Degradation** - Server starts even with invalid credentials, flagging the issue clearly
- **Comprehensive Logging** - Debug-friendly logging system

## 🔧 **Installation & Setup**

### **1. Install from PyPI**
```bash
pip install tiktok-ads-mcp
```

### **2. Set up environment variables**
Copy the example environment file and configure your TikTok API credentials:
```bash
# Create .env file from template
cp env.template .env
```

Edit the `.env` file with your TikTok API credentials:
```bash
# Required TikTok API credentials
TIKTOK_APP_ID="your_app_id_here"
TIKTOK_SECRET="your_app_secret_here"
TIKTOK_ACCESS_TOKEN="your_access_token_here"

# Optional performance settings
TOKEN_CACHE_ENABLED=true
TIKTOK_API_RATE_LIMIT=1000
TIKTOK_REQUEST_TIMEOUT=30
```

**Note**: The `.env` file is git-ignored and will not be shared.

### **3. Development Installation**
For development or local testing:
```bash
git clone https://github.com/ysntony/tiktok-ads-mcp.git
cd tiktok-ads-mcp
pip install -e .
```

## 🚀 **Usage**

### **Running the MCP Server**

After installation, run the MCP server with a single command:
```bash
tiktok-ads-mcp
```

### **MCP Client Integration**

Configure your MCP client (like Claude Desktop, Cursor, etc.) to use the installed command:

```json
{
  "mcpServers": {
    "tiktok-ads": {
      "command": "tiktok-ads-mcp",
      "args": []
    }
  }
}
```

### **Development Mode**

For development or testing without installation:
```bash
python examples/basic_usage.py
```

## 📋 **Available MCP Tools**

This server exposes several tools for interacting with the TikTok Ads API:

- **`get_advertisers`** - Get all advertiser accounts
- **`get_campaigns_v2`** - Get campaigns with optional filters
- **`get_insights`** - Get performance insights and metrics
- **`health_check`** - Check API connectivity and server health
- **`validate_token`** - Validate API credentials and return account info
- **`get_auth_info`** - Get comprehensive authentication status

For detailed function parameters, return values, and use cases, see the [MCP Usage Guide](MCP_USAGE.md).

## 🏗️ **Project Structure**

```
tiktok-ads-mcp/
├── tiktok_ads_mcp/           # The main Python package
│   ├── __init__.py          # Package initialization
│   ├── server.py            # Core MCP server implementation
│   ├── client.py            # TikTok API client logic
│   ├── config.py            # Configuration management (.env loader)
│   └── main.py              # Command-line entry point
├── examples/                 # Usage examples
│   └── basic_usage.py
├── .gitignore               # Files to be ignored by Git
├── LICENSE                  # Project License
├── MCP_USAGE.md             # Detailed function documentation
├── pyproject.toml           # Project definition and dependencies
├── env.template             # Template for environment variables
└── README.md                # This file
```

## 🔑 **Getting TikTok API Credentials**

1. Visit the [TikTok Business API Portal](https://business-api.tiktok.com/portal/)
2. Create a new app or use an existing one
3. Generate an access token with the following scopes:
   - User Info Basic
   - Ad Management Read
   - Campaign Management Read
   - Reporting Read

**Note**: This MCP server is **read-only** and will not modify your campaigns or ad data.

## 🤝 **Contributing**

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**
3. **Add comprehensive tests for your changes**
4. **Ensure all code is formatted and passes linting checks**
5. **Submit a pull request with a clear description of your changes**

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 **Links**

- **PyPI Package**: https://pypi.org/project/tiktok-ads-mcp/
- **GitHub Repository**: https://github.com/ysntony/tiktok-ads-mcp
- **Documentation**: [MCP Usage Guide](MCP_USAGE.md)