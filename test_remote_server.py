#!/usr/bin/env python3
"""Test script for TikTok Ads MCP Remote Server

This script tests the remote server functionality without requiring full installation.
It simulates Claude Connector integration and validates MCP protocol compliance.
"""

import json
import logging
import os
import sys
import tempfile
import time
from typing import Dict, Any

# Add current directory to Python path
sys.path.insert(0, '.')

# Mock the MCP dependencies for testing
class MockFastMCP:
    def __init__(self, name: str):
        self.name = name
        self.tools = []
        
    def tool(self):
        def decorator(func):
            self.tools.append(func)
            return func
        return decorator
    
    def run(self, transport: str):
        print(f"Mock MCP server '{self.name}' running with {transport} transport")

class MockContext:
    pass

# Mock modules
sys.modules['mcp'] = type(sys)('mcp')
sys.modules['mcp.server'] = type(sys)('mcp.server')
sys.modules['mcp.server.fastmcp'] = type(sys)('mcp.server.fastmcp')
sys.modules['mcp.server'].FastMCP = MockFastMCP
sys.modules['mcp.server.fastmcp'].Context = MockContext

# Set up test environment
os.environ['TIKTOK_APP_ID'] = 'test_app_id'
os.environ['TIKTOK_SECRET'] = 'test_secret'
os.environ['TIKTOK_ACCESS_TOKEN'] = 'test_access_token'

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all modules can be imported"""
    try:
        from tiktok_ads_mcp.config import config
        logger.info("✓ Config module imported successfully")
        
        # Mock the client for testing
        class MockTikTokAdsClient:
            def __init__(self):
                pass
        
        sys.modules['tiktok_ads_mcp.client'].TikTokAdsClient = MockTikTokAdsClient
        
        from tiktok_ads_mcp import auth
        logger.info("✓ Auth module imported successfully")
        
        return True
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")
        return False

def test_oauth_manager():
    """Test OAuth manager functionality"""
    try:
        from tiktok_ads_mcp.auth import OAuthManager
        
        manager = OAuthManager()
        
        # Test client registration
        registration_data = {
            "client_name": "Claude",
            "redirect_uris": ["https://claude.ai/api/mcp/auth_callback"],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"]
        }
        
        client = manager.register_client(registration_data)
        logger.info(f"✓ OAuth client registered: {client.client_id}")
        
        # Test authorization code generation
        code = manager.generate_authorization_code(
            client.client_id,
            "https://claude.ai/api/mcp/auth_callback"
        )
        logger.info(f"✓ Authorization code generated: {code[:10]}...")
        
        # Test token exchange
        token = manager.exchange_code_for_token(
            code,
            client.client_id,
            client.client_secret,
            "https://claude.ai/api/mcp/auth_callback"
        )
        logger.info(f"✓ Access token issued: {token.access_token[:10]}...")
        
        # Test token validation
        validated_token = manager.validate_access_token(token.access_token)
        logger.info("✓ Access token validated successfully")
        
        # Test token refresh
        new_token = manager.refresh_access_token(token.refresh_token)
        logger.info(f"✓ Token refreshed: {new_token.access_token[:10]}...")
        
        return True
    except Exception as e:
        logger.error(f"✗ OAuth manager test failed: {e}")
        return False

def test_mcp_protocol():
    """Test MCP protocol compliance"""
    try:
        from tiktok_ads_mcp.remote_server import MCPRequest, MCPResponse, MCPTool, MCP_TOOLS
        
        # Test MCP request/response models
        request = MCPRequest(
            id="test-1",
            method="tools/list",
            params={}
        )
        logger.info(f"✓ MCP request created: {request.method}")
        
        response = MCPResponse(
            id=request.id,
            result={"tools": [tool.dict() for tool in MCP_TOOLS]}
        )
        logger.info(f"✓ MCP response created with {len(MCP_TOOLS)} tools")
        
        # Validate tool definitions
        for tool in MCP_TOOLS:
            assert tool.name
            assert tool.description
            assert tool.inputSchema
            logger.info(f"  ✓ Tool validated: {tool.name}")
        
        return True
    except Exception as e:
        logger.error(f"✗ MCP protocol test failed: {e}")
        return False

def test_server_endpoints():
    """Test server endpoint definitions"""
    try:
        # Import without running the server
        spec_file = 'tiktok_ads_mcp/remote_server.py'
        with open(spec_file, 'r') as f:
            content = f.read()
            
        # Check for required endpoints
        required_endpoints = [
            '/.well-known/mcp_server',
            '/mcp',
            '/oauth/register', 
            '/oauth/authorize',
            '/oauth/token',
            '/health'
        ]
        
        for endpoint in required_endpoints:
            if f'"{endpoint}"' in content or f"'{endpoint}'" in content:
                logger.info(f"✓ Endpoint found: {endpoint}")
            else:
                logger.error(f"✗ Endpoint missing: {endpoint}")
                return False
        
        # Check for required MCP methods
        required_methods = [
            'initialize',
            'tools/list',
            'tools/call'
        ]
        
        for method in required_methods:
            if method in content:
                logger.info(f"✓ MCP method found: {method}")
            else:
                logger.error(f"✗ MCP method missing: {method}")
                return False
        
        return True
    except Exception as e:
        logger.error(f"✗ Server endpoint test failed: {e}")
        return False

def test_deployment_config():
    """Test deployment configuration files"""
    try:
        # Test Docker files
        docker_files = [
            'Dockerfile',
            'Dockerfile.prod', 
            'docker-compose.yml',
            'nginx.conf'
        ]
        
        for file in docker_files:
            if os.path.exists(file):
                logger.info(f"✓ Deployment file exists: {file}")
                
                # Basic validation
                with open(file, 'r') as f:
                    content = f.read()
                    if len(content) > 100:  # Non-empty file
                        logger.info(f"  ✓ File has content: {file}")
                    else:
                        logger.warning(f"  ⚠ File seems empty: {file}")
            else:
                logger.error(f"✗ Deployment file missing: {file}")
                return False
        
        # Test deployment script
        if os.path.exists('deploy.sh') and os.access('deploy.sh', os.X_OK):
            logger.info("✓ Deployment script exists and is executable")
        else:
            logger.error("✗ Deployment script missing or not executable")
            return False
        
        return True
    except Exception as e:
        logger.error(f"✗ Deployment config test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and return overall result"""
    logger.info("=" * 60)
    logger.info("TikTok Ads MCP Remote Server Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("OAuth Manager", test_oauth_manager),
        ("MCP Protocol", test_mcp_protocol),
        ("Server Endpoints", test_server_endpoints),
        ("Deployment Config", test_deployment_config),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning: {test_name}")
        logger.info("-" * 40)
        
        try:
            if test_func():
                logger.info(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Passed: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("Your TikTok Ads MCP Remote Server is ready for deployment!")
    else:
        logger.error(f"❌ {total - passed} tests failed")
        logger.error("Please fix the issues before deploying")
    
    logger.info("\nNext steps:")
    logger.info("1. Set up your TikTok API credentials")
    logger.info("2. Choose a deployment method (Docker recommended)")
    logger.info("3. Run: ./deploy.sh --type production --platform docker")
    logger.info("4. Add your server URL to Claude via Settings > Connectors")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)