# TikTok Ads MCP Server

A **pure MCP (Model Context Protocol)** server for TikTok Business API integration, designed for AI-first interactions. Inspired by the [meta-ads-mcp](https://github.com/pipeboard-co/meta-ads-mcp.git) project architecture.

## 🎯 **Pure MCP Architecture**

This project follows the **pure MCP server design philosophy**:
- **AI-First**: Designed specifically for AI model consumption.
- **Single Interface**: MCP protocol only - no extra CLI, web UI, or other human interfaces.
- **Lightweight**: Minimal dependencies defined in `pyproject.toml` for core functionality.
- **Production-Ready**: Enterprise-grade reliability and error handling.

## 🚀 **Key Features**

### 🔐 **Enhanced Authentication System**
- **Robust Local Authentication** - Secure `.env`-based credential management.
- **Token Validation** - Comprehensive API credential validation on startup.
- **Smart Caching** - Performance-optimized response caching.
- **Rate Limiting** - Built-in API rate limiting protection.

### 🛡️ **Production-Ready Error Handling**
- **Custom Exception Types** - `TikTokAuthenticationError` and `TikTokAPIError`.
- **Detailed Error Messages** - Clear error descriptions with actionable suggestions.
- **Graceful Degradation** - Server starts even with invalid credentials, flagging the issue clearly.
- **Comprehensive Logging** - Debug-friendly logging system.

## 🔧 Installation & Setup

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd tiktok-ads-mcp
    ```

2.  **Set up environment variables**:
    Copy the example environment file. This is where you will store your secret credentials.
    ```bash
    cp .env.example .env
    ```
    Edit the `.env` file with your TikTok API credentials. **This file is git-ignored and will not be shared.**
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

3.  **Install the package**:
    Install the project in "editable" mode. This command reads the `pyproject.toml` file, installs all dependencies, and makes the `tiktok-ads-mcp` command available in your terminal.
    ```bash
    pip install -e .
    ```

## 🚀 Usage

### **1. Running as a Command (Recommended)**

After installation, you can run the MCP server from anywhere with a single command:
```bash 
tiktok-ads-mcp
```

### **2. Running for Development**

For development or testing, you can also run the server directly from the example script without installation:
```bash
python examples/basic_usage.py
```

### **3. MCP Client Integration**
Configure your MCP client (like Claude Desktop) to use the installed command. This is the most robust method.
```JSON
{
  "mcpServers": {
    "tiktok-ads": {
      "command": "tiktok-ads-mcp",
      "args": [],
    }
  }
}
```

## 📋 Available MCP Tools
This server exposes several tools for interacting with the TikTok Ads API.

-- **get_advertisers** - Get all advertiser accounts.
-- **get_campaigns** - Get campaigns with optional filters.
-- **get_insights** - Get performance insights and metrics.
-- **health_check** - Check API connectivity and server health.
-- **validate_token** - Validate API credentials and return account info.
-- **get_auth_info** - Get comprehensive authentication status.
For a detailed guide on all function parameters, return values, and use cases, please see the MCP Usage Guide.

## 🏗️ Project Structure
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
├── .env.template            # Template for environment variables
└── README.md                # This file

## 🤝 Contributing
-- **Fork the repository.**
-- **Create a feature branch.**
-- **Add comprehensive tests for your changes.**
-- **Ensure all code is formatted and passes linting checks.**
-- **Submit a pull request with a clear description of your changes.**

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.