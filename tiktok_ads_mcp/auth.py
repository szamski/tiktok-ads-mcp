#!/usr/bin/env python3
"""OAuth 2.0 Authentication Module for TikTok Ads MCP Remote Server

Implements OAuth 2.0 with Dynamic Client Registration (DCR) support for Claude Connector integration.
Provides secure authentication flow with token management and refresh capabilities.
"""

import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode, urlparse

from authlib.oauth2 import OAuth2Error
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class OAuthClient(BaseModel):
    """OAuth client registration model"""
    client_id: str
    client_secret: str
    client_name: str
    redirect_uris: List[str]
    grant_types: List[str] = ["authorization_code", "refresh_token"]
    response_types: List[str] = ["code"]
    scope: str = "read"
    created_at: datetime
    expires_at: Optional[datetime] = None

class OAuthToken(BaseModel):
    """OAuth token model"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    refresh_token: Optional[str] = None
    scope: str = "read"
    created_at: datetime

class AuthorizationCode(BaseModel):
    """Authorization code model"""
    code: str
    client_id: str
    redirect_uri: str
    scope: str
    state: Optional[str] = None
    created_at: datetime
    expires_at: datetime

class OAuthManager:
    """OAuth 2.0 manager with Dynamic Client Registration support"""
    
    def __init__(self):
        # In production, these would be stored in a database
        self.clients: Dict[str, OAuthClient] = {}
        self.authorization_codes: Dict[str, AuthorizationCode] = {}
        self.access_tokens: Dict[str, OAuthToken] = {}
        self.refresh_tokens: Dict[str, str] = {}  # refresh_token -> access_token
        
        # Claude-specific configuration
        self.claude_redirect_uris = [
            "https://claude.ai/api/mcp/auth_callback",
            "https://claude.com/api/mcp/auth_callback"
        ]
        
        # Token expiration settings
        self.code_expiration_minutes = 10
        self.token_expiration_minutes = 60
        
    def generate_client_credentials(self) -> Tuple[str, str]:
        """Generate client ID and secret"""
        client_id = f"tiktok-ads-mcp-{secrets.token_urlsafe(16)}"
        client_secret = secrets.token_urlsafe(32)
        return client_id, client_secret
    
    def register_client(self, registration_data: Dict) -> OAuthClient:
        """Register a new OAuth client (RFC 7591 Dynamic Client Registration)"""
        try:
            # Validate required fields
            required_fields = ["redirect_uris", "client_name"]
            for field in required_fields:
                if field not in registration_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate redirect URIs for Claude
            redirect_uris = registration_data["redirect_uris"]
            if not isinstance(redirect_uris, list):
                raise ValueError("redirect_uris must be an array")
            
            # Check if at least one URI is valid for Claude
            valid_uris = set(redirect_uris) & set(self.claude_redirect_uris)
            if not valid_uris:
                raise ValueError("At least one redirect URI must be a valid Claude callback URL")
            
            # Generate client credentials
            client_id, client_secret = self.generate_client_credentials()
            
            # Create client record
            client = OAuthClient(
                client_id=client_id,
                client_secret=client_secret,
                client_name=registration_data["client_name"],
                redirect_uris=redirect_uris,
                grant_types=registration_data.get("grant_types", ["authorization_code", "refresh_token"]),
                response_types=registration_data.get("response_types", ["code"]),
                scope=registration_data.get("scope", "read"),
                created_at=datetime.utcnow()
            )
            
            # Store client
            self.clients[client_id] = client
            
            logger.info(f"Registered OAuth client: {client_id} for {client.client_name}")
            return client
            
        except Exception as e:
            logger.error(f"Client registration failed: {e}")
            raise ValueError(f"Client registration failed: {str(e)}")
    
    def validate_client(self, client_id: str, client_secret: Optional[str] = None) -> OAuthClient:
        """Validate client credentials"""
        if client_id not in self.clients:
            raise OAuth2Error(error="invalid_client", description="Unknown client")
        
        client = self.clients[client_id]
        
        if client_secret and client.client_secret != client_secret:
            raise OAuth2Error(error="invalid_client", description="Invalid client secret")
        
        return client
    
    def generate_authorization_code(
        self, 
        client_id: str, 
        redirect_uri: str, 
        scope: str = "read",
        state: Optional[str] = None
    ) -> str:
        """Generate authorization code"""
        try:
            # Validate client
            client = self.validate_client(client_id)
            
            # Validate redirect URI
            if redirect_uri not in client.redirect_uris:
                raise OAuth2Error(
                    error="invalid_request", 
                    description="Invalid redirect URI"
                )
            
            # Generate authorization code
            code = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(minutes=self.code_expiration_minutes)
            
            # Store authorization code
            auth_code = AuthorizationCode(
                code=code,
                client_id=client_id,
                redirect_uri=redirect_uri,
                scope=scope,
                state=state,
                created_at=datetime.utcnow(),
                expires_at=expires_at
            )
            
            self.authorization_codes[code] = auth_code
            
            # Clean up expired codes
            self._cleanup_expired_codes()
            
            logger.info(f"Generated authorization code for client {client_id}")
            return code
            
        except OAuth2Error:
            raise
        except Exception as e:
            logger.error(f"Authorization code generation failed: {e}")
            raise OAuth2Error(
                error="server_error", 
                description=f"Code generation failed: {str(e)}"
            )
    
    def exchange_code_for_token(
        self, 
        code: str, 
        client_id: str, 
        client_secret: str,
        redirect_uri: str
    ) -> OAuthToken:
        """Exchange authorization code for access token"""
        try:
            # Validate client
            client = self.validate_client(client_id, client_secret)
            
            # Validate authorization code
            if code not in self.authorization_codes:
                raise OAuth2Error(error="invalid_grant", description="Invalid authorization code")
            
            auth_code = self.authorization_codes[code]
            
            # Check if code is expired
            if datetime.utcnow() > auth_code.expires_at:
                del self.authorization_codes[code]
                raise OAuth2Error(error="invalid_grant", description="Authorization code expired")
            
            # Validate client ID and redirect URI
            if auth_code.client_id != client_id:
                raise OAuth2Error(error="invalid_grant", description="Client ID mismatch")
            
            if auth_code.redirect_uri != redirect_uri:
                raise OAuth2Error(error="invalid_grant", description="Redirect URI mismatch")
            
            # Generate tokens
            access_token = secrets.token_urlsafe(32)
            refresh_token = secrets.token_urlsafe(32)
            
            # Create token record
            token = OAuthToken(
                access_token=access_token,
                token_type="Bearer",
                expires_in=self.token_expiration_minutes * 60,
                refresh_token=refresh_token,
                scope=auth_code.scope,
                created_at=datetime.utcnow()
            )
            
            # Store tokens
            self.access_tokens[access_token] = token
            self.refresh_tokens[refresh_token] = access_token
            
            # Remove used authorization code
            del self.authorization_codes[code]
            
            # Clean up expired tokens
            self._cleanup_expired_tokens()
            
            logger.info(f"Issued access token for client {client_id}")
            return token
            
        except OAuth2Error:
            raise
        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            raise OAuth2Error(
                error="server_error", 
                description=f"Token exchange failed: {str(e)}"
            )
    
    def refresh_access_token(self, refresh_token: str) -> OAuthToken:
        """Refresh access token using refresh token"""
        try:
            # Validate refresh token
            if refresh_token not in self.refresh_tokens:
                raise OAuth2Error(error="invalid_grant", description="Invalid refresh token")
            
            # Get current access token
            old_access_token = self.refresh_tokens[refresh_token]
            
            if old_access_token not in self.access_tokens:
                raise OAuth2Error(error="invalid_grant", description="Associated access token not found")
            
            old_token = self.access_tokens[old_access_token]
            
            # Generate new access token
            new_access_token = secrets.token_urlsafe(32)
            
            # Create new token record
            new_token = OAuthToken(
                access_token=new_access_token,
                token_type="Bearer",
                expires_in=self.token_expiration_minutes * 60,
                refresh_token=refresh_token,  # Keep same refresh token
                scope=old_token.scope,
                created_at=datetime.utcnow()
            )
            
            # Update token storage
            self.access_tokens[new_access_token] = new_token
            self.refresh_tokens[refresh_token] = new_access_token
            
            # Remove old access token
            if old_access_token in self.access_tokens:
                del self.access_tokens[old_access_token]
            
            logger.info("Refreshed access token")
            return new_token
            
        except OAuth2Error:
            raise
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise OAuth2Error(
                error="server_error", 
                description=f"Token refresh failed: {str(e)}"
            )
    
    def validate_access_token(self, access_token: str) -> OAuthToken:
        """Validate access token"""
        if access_token not in self.access_tokens:
            raise OAuth2Error(error="invalid_token", description="Invalid access token")
        
        token = self.access_tokens[access_token]
        
        # Check if token is expired
        expires_at = token.created_at + timedelta(seconds=token.expires_in)
        if datetime.utcnow() > expires_at:
            # Remove expired token
            del self.access_tokens[access_token]
            if token.refresh_token and token.refresh_token in self.refresh_tokens:
                del self.refresh_tokens[token.refresh_token]
            raise OAuth2Error(error="invalid_token", description="Access token expired")
        
        return token
    
    def revoke_token(self, token: str) -> bool:
        """Revoke access or refresh token"""
        try:
            # Try as access token first
            if token in self.access_tokens:
                token_obj = self.access_tokens[token]
                del self.access_tokens[token]
                
                # Also remove associated refresh token
                if token_obj.refresh_token and token_obj.refresh_token in self.refresh_tokens:
                    del self.refresh_tokens[token_obj.refresh_token]
                
                logger.info("Revoked access token")
                return True
            
            # Try as refresh token
            if token in self.refresh_tokens:
                access_token = self.refresh_tokens[token]
                del self.refresh_tokens[token]
                
                # Also remove associated access token
                if access_token in self.access_tokens:
                    del self.access_tokens[access_token]
                
                logger.info("Revoked refresh token")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Token revocation failed: {e}")
            return False
    
    def _cleanup_expired_codes(self):
        """Clean up expired authorization codes"""
        now = datetime.utcnow()
        expired_codes = [
            code for code, auth_code in self.authorization_codes.items()
            if now > auth_code.expires_at
        ]
        
        for code in expired_codes:
            del self.authorization_codes[code]
        
        if expired_codes:
            logger.info(f"Cleaned up {len(expired_codes)} expired authorization codes")
    
    def _cleanup_expired_tokens(self):
        """Clean up expired access tokens"""
        now = datetime.utcnow()
        expired_tokens = []
        
        for access_token, token in self.access_tokens.items():
            expires_at = token.created_at + timedelta(seconds=token.expires_in)
            if now > expires_at:
                expired_tokens.append(access_token)
        
        for access_token in expired_tokens:
            token = self.access_tokens[access_token]
            del self.access_tokens[access_token]
            
            # Also remove associated refresh token
            if token.refresh_token and token.refresh_token in self.refresh_tokens:
                del self.refresh_tokens[token.refresh_token]
        
        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired access tokens")
    
    def get_client_info(self, client_id: str) -> Optional[Dict]:
        """Get client information for registration response"""
        if client_id not in self.clients:
            return None
        
        client = self.clients[client_id]
        return {
            "client_id": client.client_id,
            "client_secret": client.client_secret,
            "client_name": client.client_name,
            "redirect_uris": client.redirect_uris,
            "grant_types": client.grant_types,
            "response_types": client.response_types,
            "token_endpoint_auth_method": "client_secret_basic",
            "scope": client.scope,
            "client_id_issued_at": int(client.created_at.timestamp()),
            "client_secret_expires_at": 0  # Never expires
        }

# Global OAuth manager instance
oauth_manager = OAuthManager()

def get_oauth_manager() -> OAuthManager:
    """Get the global OAuth manager instance"""
    return oauth_manager