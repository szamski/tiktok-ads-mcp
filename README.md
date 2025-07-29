# TikTok Ads MCP

A comprehensive Model Context Protocol (MCP) server for interacting with the TikTok Business API. This package provides a complete interface to access TikTok advertising campaigns, ad groups, ads, and generate detailed performance reports.

## Features

- **Read-Only TikTok Business API Integration**: Access all major TikTok advertising endpoints for data retrieval
- **6 Comprehensive Tools**: Business centers, ad accounts, campaigns, ad groups, ads, and reports
- **Advanced Filtering**: Powerful filtering options for all data retrieval operations
- **Multi-Advertiser Support**: Handle multiple advertiser accounts in a single request
- **Flexible Reporting**: Generate detailed performance reports with custom dimensions and metrics
- **Real-time Data**: Access live advertising data and performance metrics
- **Error Handling**: Comprehensive error handling and validation
- **Modular Architecture**: Clean, maintainable code structure
- **Safe Operations**: All tools are read-only and will not modify your campaigns or ad data

## Available Tools

1. **get_business_centers** - Retrieve business centers accessible by your access token
2. **get_authorized_ad_accounts** - Get all authorized advertiser accounts
3. **get_campaigns** - Retrieve campaigns with comprehensive filtering options
4. **get_ad_groups** - Get ad groups with advanced filtering and targeting options
5. **get_ads** - Retrieve ads with detailed creative and performance data
6. **get_reports** - Generate comprehensive performance reports and analytics

## Prerequisites

- Python 3.8 or higher
- TikTok Business API access
- Valid API credentials (app ID, secret, access token)

## Quick Start

### Installation

```bash
# Install the latest version from PyPI
pip install tiktok-ads-mcp
```

### Configuration

1. **Set up environment variables** in your MCP client configuration:

```json
{
  "mcpServers": {
    "tiktok-ads": {
      "command": "python",
      "args": ["-m", "tiktok_ads_mcp"],
      "env": {
        "TIKTOK_APP_ID": "your_app_id",
        "TIKTOK_SECRET": "your_secret",
        "TIKTOK_ACCESS_TOKEN": "your_access_token"
      }
    }
  }
}
```

2. **Required credentials**:
   - `TIKTOK_APP_ID`: Your TikTok app ID
   - `TIKTOK_SECRET`: Your TikTok app secret
   - `TIKTOK_ACCESS_TOKEN`: Your access token

### Usage

Once configured, you can use the MCP tools through your MCP client (like Cursor, Claude Desktop, etc.):

- **Get business centers and advertiser accounts** to discover available accounts
- **Retrieve campaigns** with filtering by status, objective, or date range
- **Access ad groups** with advanced targeting and optimization settings
- **View ads** with detailed creative and performance data
- **Generate reports** with custom dimensions, metrics, and time ranges
- **Access real-time advertising data** and performance metrics

## API Coverage

This MCP server provides **read-only** access to the TikTok Business API:

### Business Management
- Business center retrieval and access
- Advertiser account information and permissions

### Campaign Management
- Campaign retrieval and filtering
- Campaign status and performance monitoring
- Campaign budget and objective information

### Ad Group Management
- Ad group retrieval and filtering
- Advanced targeting and optimization settings
- Performance monitoring and analysis

### Ad Management
- Ad retrieval and filtering
- Creative asset information
- Performance tracking and analysis

### Reporting & Analytics
- Basic performance reports
- Audience insights reports
- Playable ads reports
- DSA (Dynamic Search Ads) reports
- Business Center reports
- GMV max ads reports

## Key Features

### Advanced Filtering
All tools support comprehensive filtering options:
- Status-based filtering (active, paused, deleted)
- Time-based filtering (creation date, modification date)
- Performance-based filtering (budget, optimization goals)
- Creative filtering (ad formats, material types)

### Modern Implementation
This package uses the official FastMCP framework for optimal performance and developer experience:

- **Automatic Schema Generation**: From Python type hints
- **Simplified Tool Registration**: Using `@app.tool()` decorators
- **Built-in Error Handling**: Consistent error responses
- **Type Safety**: Full parameter validation from type hints
- **Future-Proof**: Part of the official MCP SDK

### Multi-Advertiser Support
- Handle multiple advertiser accounts in single requests
- Cross-advertiser reporting and analytics
- Unified data access across accounts

### Flexible Reporting
- Custom dimensions and metrics
- Multiple report types and data levels
- Time-based and lifetime metrics
- Aggregated and detailed views

### Error Handling
- Comprehensive parameter validation
- Detailed error messages and suggestions
- Graceful handling of API limitations
- Rate limiting and retry logic

## Documentation

- **MCP_USAGE.md**: Comprehensive usage guide with examples
- **TikTok Business API**: Official API documentation
- **Project Wiki**: Additional resources and guides

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests and documentation
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
1. Check the [MCP_USAGE.md](MCP_USAGE.md) documentation
2. Review the [TikTok Business API documentation](https://developers.tiktok.com/doc/tiktok-business-api)
3. Open an issue on the GitHub repository
4. Contact the development team

## Changelog

### v0.1.2 (Current)
- **FastMCP Implementation**: Modern MCP server using official FastMCP framework
- **70% Code Reduction**: Compared to traditional MCP implementations
- **Automatic Schema Generation**: From Python type hints
- **Simplified Tool Registration**: Using `@app.tool()` decorators
- **Enhanced Error Handling**: Built-in error handling with consistent responses
- **Type Safety**: Full parameter validation from type hints
- **Future-Proof**: Part of the official MCP SDK

### v0.1.1
- Complete implementation of all 6 tools
- Advanced filtering and reporting capabilities
- Multi-advertiser support
- Comprehensive error handling
- Modular tools architecture
- Complete documentation and usage guides

### v0.1.0
- Initial release with basic MCP server structure
- Core API client implementation
- Basic authentication and configuration