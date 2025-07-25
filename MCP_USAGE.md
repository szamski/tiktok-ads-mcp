# 🚀 TikTok Business API MCP Usage Guide

## Overview

This guide provides practical examples and reference material for using the TikTok Business API MCP (Model Context Protocol) server. It's designed for users who have the server installed and want to interact with it through an MCP client.

## 🛠️ Setup

Before using these tools, ensure you have completed the following setup:

1. **Installed the Package**: The server should be installed via `pip`. If you haven't done this, refer to the `README.md` for instructions.
2. **Configured Credentials**: A `.env` file with your TikTok API credentials must exist in the project's root directory.
3. **Connected MCP Client**: Your MCP client (like Claude Desktop, Cursor, etc.) should be configured to connect to the server.

---

## 🔧 MCP Client Configuration

In your MCP client, configure a new server with the following settings. The command should be `tiktok-ads-mcp`, which is made available after you install the package.

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

---

## 📊 Available Tools

### 1. `get_advertisers`

Get all advertiser accounts accessible by your access token.

**Parameters:** None

**Usage:**
```python
get_advertisers()
```

**Example Return:**
```json
{
  "success": true,
  "count": 1,
  "advertisers": [
    {
      "advertiser_id": "Your Ad Account ID",
      "advertiser_name": "Your Business Name",
      "status": "STATUS_ENABLE"
    }
  ]
}
```

### 2. `get_campaigns`

Get campaigns for a specific advertiser, with optional filters.

**Parameters:**
- `advertiser_id` (string, required): Your TikTok advertiser ID
- `filters` (object, optional): A dictionary for filtering. e.g., `{"status": "CAMPAIGN_STATUS_ENABLE"}`

**Usage:**
```python
get_campaigns_v2(
    advertiser_id="Your Ad Account ID"
)
```

### 3. `get_insights`

Get performance insights and metrics for campaigns, ad groups, or ads.

**Parameters:**
- `advertiser_id` (string, required): Your TikTok advertiser ID
- `start_date` (string, required): Start date in YYYY-MM-DD format
- `end_date` (string, required): End date in YYYY-MM-DD format
- `data_level` (string, optional): "AUCTION_CAMPAIGN", "AUCTION_ADGROUP", or "AUCTION_AD". Default is "AUCTION_CAMPAIGN"
- `metrics` (array, optional): A list of metrics to retrieve

**Usage:**
```python
get_insights(
    advertiser_id="Your Ad Account ID",
    start_date="2025-01-01", 
    end_date="2025-01-07",
    data_level="AUCTION_CAMPAIGN",
    metrics=["spend", "impressions", "clicks", "ctr"]
)
```

### 4. `health_check`

Check the API connectivity and server health.

**Parameters:** None

**Usage:**
```python
health_check()
```

### 5. `validate_token`

Validate the current API access token and return details about its permissions.

**Parameters:** None

**Usage:**
```python
validate_token()
```

### 6. `get_auth_info`

Get a comprehensive status of the server's authentication and configuration.

**Parameters:** None

**Usage:**
```python
get_auth_info()
```

---

## 📋 Available Metrics Reference

A list of common metrics you can request with the `get_insights` tool.

### Standard Metrics

- `spend`
- `impressions`
- `clicks`
- `ctr`
- `cpm`
- `cpc`
- `conversions`
- `conversion_rate`

### Video Metrics

- `video_play_actions`
- `video_watched_2s`
- `video_watched_6s`
- `video_views_p25` / `p50` / `p75` / `p100`

---

## 🚨 Troubleshooting

### "command not found: tiktok-ads-mcp"

This means the package was not installed correctly or your terminal's path is not configured to find packages installed by pip. Ensure you have run `pip install -e .` from the project root.

### Authentication Errors

Run `get_auth_info()` to see the status of your loaded credentials. Most issues can be traced to an incorrect or expired key in your `.env` file.

### No Data Returned

For `get_insights`, double-check that your date range is valid and that campaigns were active during that period.