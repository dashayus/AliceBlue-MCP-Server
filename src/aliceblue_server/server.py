# server.py
from pydantic import BaseModel, Field
from mcp.server.fastmcp import Context, FastMCP
from smithery.decorators import smithery
import requests
import hashlib
import time
from typing import Optional, Union
import json
import asyncio

# Try both possible base URLs
BASE_URLS = [
    "https://ant.aliceblueonline.com",
    "https://a3.aliceblueonline.com"
]

# Configuration schema for session
class ConfigSchema(BaseModel):
    user_id: str = Field(description="Your AliceBlue User ID")
    auth_code: str = Field(description="Your AliceBlue Auth Code") 
    api_secret: str = Field(description="Your AliceBlue API Secret")

@smithery.server(config_schema=ConfigSchema)
def create_server():
    """Create and configure the AliceBlue MCP server."""
    
    server = FastMCP("AliceBlue Trading")

    class AliceBlue:
        def __init__(self, user_id: str, auth_code: str, api_secret: str):
            self.user_id = user_id
            self.auth_code = auth_code
            self.api_secret = api_secret
            self.user_session = None
            self.headers = None
            self.base_url = None
            self.is_authenticated = False

        def test_authentication(self):
            """Test authentication with different base URLs"""
            for base_url in BASE_URLS:
                try:
                    print(f"Testing authentication with: {base_url}")
                    
                    # Prepare checksum
                    raw_string = f"{self.user_id}{self.auth_code}{self.api_secret}"
                    checksum = hashlib.sha256(raw_string.encode()).hexdigest()

                    url = f"{base_url}/open-api/od/v1/vendor/getUserDetails"
                    payload = {"checkSum": checksum}

                    response = requests.post(url, json=payload, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("stat") == "Ok":
                            self.user_session = data["userSession"]
                            self.headers = {
                                "Authorization": f"Bearer {self.user_session}",
                                "Content-Type": "application/json"
                            }
                            self.base_url = base_url
                            self.is_authenticated = True
                            print(f"✅ Authenticated successfully with {base_url}")
                            return True
                    
                    print(f"❌ Failed with {base_url}: {response.status_code} - {response.text}")
                    
                except Exception as e:
                    print(f"❌ Error with {base_url}: {str(e)}")
                    continue
            
            return False

        def get_session(self):
            return self.user_session

        def make_request(self, endpoint, method="GET", payload=None):
            """Make API request with current session"""
            if not self.is_authenticated:
                raise Exception("Not authenticated")
            
            url = f"{self.base_url}{endpoint}"
            
            try:
                if method == "GET":
                    response = requests.get(url, headers=self.headers, timeout=10)
                else:
                    response = requests.post(url, headers=self.headers, json=payload, timeout=10)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    raise Exception(f"API Error {response.status_code}: {response.text}")
                    
            except Exception as e:
                raise Exception(f"Request failed: {str(e)}")

        # Mock data methods for testing
        def get_mock_profile(self):
            return {
                "stat": "Ok",
                "data": {
                    "clientName": "Test User",
                    "email": "test@example.com",
                    "clientId": self.user_id,
                    "exchanges": ["NSE", "BSE"]
                }
            }

        def get_mock_holdings(self):
            return {
                "stat": "Ok",
                "data": [
                    {
                        "symbol": "RELIANCE",
                        "quantity": 10,
                        "averagePrice": 2450.50,
                        "currentPrice": 2500.75
                    }
                ]
            }

        def get_mock_positions(self):
            return {
                "stat": "Ok",
                "data": {
                    "net": [],
                    "day": [
                        {
                            "symbol": "INFY",
                            "quantity": 5,
                            "averagePrice": 1650.25
                        }
                    ]
                }
            }

        def test_connection(self):
            """Test connection with fallback to mock data"""
            try:
                if self.test_authentication():
                    # Try to get real profile data
                    profile_data = self.make_request("/open-api/od/v1/profile")
                    return {
                        "status": "success",
                        "message": "Successfully connected to AliceBlue API",
                        "session_active": True,
                        "user_id": self.user_id,
                        "session_id": self.user_session,
                        "base_url": self.base_url,
                        "data_source": "live"
                    }
                else:
                    # Fallback to mock data
                    return {
                        "status": "mock",
                        "message": "Using mock data - Authentication failed but server is running",
                        "session_active": False,
                        "user_id": self.user_id,
                        "data_source": "mock"
                    }
            except Exception as e:
                # Fallback to mock data on any error
                return {
                    "status": "mock",
                    "message": f"Using mock data - {str(e)}",
                    "session_active": False,
                    "user_id": self.user_id,
                    "data_source": "mock"
                }

    def get_alice_client(ctx: Context):
        """Get or create AliceBlue client"""
        if hasattr(ctx.session_state, 'alice_client'):
            return ctx.session_state.alice_client

        config = ctx.session_config
        
        alice = AliceBlue(
            user_id=config.user_id,
            auth_code=config.auth_code, 
            api_secret=config.api_secret
        )
        
        ctx.session_state.alice_client = alice
        return alice

    # Tools
    @server.tool()
    def test_connection(ctx: Context) -> dict:
        """Test connection to AliceBlue API"""
        try:
            alice = get_alice_client(ctx)
            return alice.test_connection()
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection test failed: {str(e)}"
            }

    @server.tool()
    def get_profile(ctx: Context) -> dict:
        """Get user profile (uses mock data if auth fails)"""
        try:
            alice = get_alice_client(ctx)
            if alice.is_authenticated:
                data = alice.make_request("/open-api/od/v1/profile")
                return {"status": "success", "data_source": "live", "data": data}
            else:
                data = alice.get_mock_profile()
                return {"status": "success", "data_source": "mock", "data": data}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_holdings(ctx: Context) -> dict:
        """Get user holdings (uses mock data if auth fails)"""
        try:
            alice = get_alice_client(ctx)
            if alice.is_authenticated:
                data = alice.make_request("/open-api/od/v1/holdings/CNC")
                return {"status": "success", "data_source": "live", "data": data}
            else:
                data = alice.get_mock_holdings()
                return {"status": "success", "data_source": "mock", "data": data}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_positions(ctx: Context) -> dict:
        """Get user positions (uses mock data if auth fails)"""
        try:
            alice = get_alice_client(ctx)
            if alice.is_authenticated:
                data = alice.make_request("/open-api/od/v1/positions")
                return {"status": "success", "data_source": "live", "data": data}
            else:
                data = alice.get_mock_positions()
                return {"status": "success", "data_source": "mock", "data": data}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def debug_auth(ctx: Context) -> dict:
        """Debug authentication issues"""
        try:
            alice = get_alice_client(ctx)
            
            # Test each base URL
            results = []
            for base_url in BASE_URLS:
                try:
                    raw_string = f"{alice.user_id}{alice.auth_code}{alice.api_secret}"
                    checksum = hashlib.sha256(raw_string.encode()).hexdigest()
                    
                    url = f"{base_url}/open-api/od/v1/vendor/getUserDetails"
                    payload = {"checkSum": checksum}
                    
                    response = requests.post(url, json=payload, timeout=10)
                    
                    results.append({
                        "base_url": base_url,
                        "status_code": response.status_code,
                        "response": response.text[:200] if response.text else "No response",
                        "success": response.status_code == 200 and "userSession" in response.text
                    })
                except Exception as e:
                    results.append({
                        "base_url": base_url,
                        "status_code": "Error",
                        "response": str(e),
                        "success": False
                    })
            
            return {
                "status": "debug",
                "user_id": alice.user_id,
                "auth_code_length": len(alice.auth_code),
                "api_secret_length": len(alice.api_secret),
                "results": results
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    return server