# TikTok Ads MCP

A comprehensive Model Context Protocol (MCP) server for interacting with the TikTok Business API. This package provides a complete interface to manage TikTok advertising campaigns, ad groups, ads, and generate detailed performance reports.

## Features

- **Complete TikTok Business API Integration**: Access all major TikTok advertising endpoints
- **6 Comprehensive Tools**: Business centers, ad accounts, campaigns, ad groups, ads, and reports
- **Advanced Filtering**: Powerful filtering options for all data retrieval operations
- **Multi-Advertiser Support**: Handle multiple advertiser accounts in a single request
- **Flexible Reporting**: Generate detailed performance reports with custom dimensions and metrics
- **Real-time Data**: Access live advertising data and performance metrics
- **Error Handling**: Comprehensive error handling and validation
- **Modular Architecture**: Clean, maintainable code structure

## Available Tools

1. **get_business_centers** - Retrieve business centers accessible by your access token
2. **get_authorized_ad_accounts** - Get all authorized advertiser accounts
3. **get_campaigns** - Retrieve campaigns with comprehensive filtering options
4. **get_ad_groups** - Get ad groups with advanced filtering and targeting options
5. **get_ads** - Retrieve ads with detailed creative and performance data
6. **get_reports** - Generate comprehensive performance reports and analytics

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ysntony/tiktok-ads-mcp.git
cd tiktok-ads-mcp

# Install in development mode
pip install -e .
```

### Configuration

1. **Set up environment variables** in your MCP client configuration:

```json
{
  "mcpServers": {
    "tiktok-ads": {
      "command": "/path/to/your/python",
      "args": ["-m", "tiktok_ads_mcp"],
      "cwd": "/path/to/tiktok-ads-mcp",
      "env": {
        "TIKTOK_APP_ID": "your_app_id",
        "TIKTOK_SECRET": "your_secret",
        "TIKTOK_ACCESS_TOKEN": "your_access_token",
        "TIKTOK_ADVERTISER_ID": "your_advertiser_id"
      }
    }
  }
}
```

2. **Required credentials**:
   - `TIKTOK_APP_ID`: Your TikTok app ID
   - `TIKTOK_SECRET`: Your TikTok app secret
   - `TIKTOK_ACCESS_TOKEN`: Your access token
   - `TIKTOK_ADVERTISER_ID`: Your advertiser ID (optional)

### Usage

Once configured, you can use the MCP tools through your MCP client (like Cursor, Claude Desktop, etc.):

- Get business centers and advertiser accounts
- Retrieve campaigns, ad groups, and ads with filtering
- Generate detailed performance reports
- Access real-time advertising data

## Project Structure

```
tiktok_ads_mcp/
├── client.py              # Core API client
├── config.py              # Configuration management
├── server.py              # MCP server implementation
├── tools/                 # Individual tool implementations
│   ├── __init__.py
│   ├── get_business_centers.py
│   ├── get_authorized_ad_accounts.py
│   ├── get_campaigns.py
│   ├── get_ad_groups.py
│   ├── get_ads.py
│   └── reports.py
└── __main__.py            # Entry point for module execution
```

## API Coverage

This MCP server provides comprehensive coverage of the TikTok Business API:

### Business Management
- Business center retrieval and management
- Advertiser account access and permissions

### Campaign Management
- Campaign creation, retrieval, and filtering
- Campaign status and performance monitoring
- Budget and objective management

### Ad Group Management
- Ad group creation and retrieval
- Advanced targeting and optimization settings
- Performance monitoring and filtering

### Ad Management
- Ad creation and retrieval
- Creative asset management
- Performance tracking and optimization

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

## Development

### Prerequisites
- Python 3.8+
- TikTok Business API access
- Valid API credentials

### Local Development
```bash
# Install development dependencies
python setup_dev.py

# Run tests
python -m pytest tests/

# Test MCP server
python test_mcp_server.py
```

### Adding New Tools
1. Create new tool file in `tiktok_ads_mcp/tools/`
2. Add function signature and implementation
3. Update `tools/__init__.py`
4. Add tool definition in `server.py`
5. Test the implementation

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
2. Review the [TikTok Business API documentation](https://developers.tiktok.com/doc/login-kit-web)
3. Open an issue on the GitHub repository
4. Contact the development team

## Changelog

### v0.1.1 (Current)
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

---

*Built with ❤️ for the growth marketing community*