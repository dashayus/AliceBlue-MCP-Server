from pydantic import BaseModel, Field
from mcp.server.fastmcp import Context, FastMCP
from smithery.decorators import smithery
import requests
import hashlib

BASE_URL = "https://a3.aliceblueonline.com"

# Configuration schema for session
class ConfigSchema(BaseModel):
    user_id: str = Field(description="Your AliceBlue User ID")
    auth_code: str = Field(description="Your AliceBlue Auth Code") 
    api_secret: str = Field(description="Your AliceBlue API Secret")

@smithery.server(config_schema=ConfigSchema)
def create_server():
    """Create and configure the AliceBlue MCP server."""
    
    # Create your FastMCP server as usual
    server = FastMCP("AliceBlue Trading")

    class AliceBlue:
        def __init__(self, user_id: str, auth_code: str, api_secret: str):
            self.user_id = user_id
            self.auth_code = auth_code
            self.api_secret = api_secret
            self.user_session = None
            self.headers = None
            self.authenticate()

        def authenticate(self):
            raw_string = f"{self.user_id}{self.auth_code}{self.api_secret}"
            checksum = hashlib.sha256(raw_string.encode()).hexdigest()

            url = f"{BASE_URL}/open-api/od/v1/vendor/getUserDetails"
            payload = {"checkSum": checksum} 

            res = requests.post(url, json=payload)

            if res.status_code != 200:
                raise Exception(f"API Error: {res.text}")

            data = res.json()
            if data.get("stat") == "Ok":
                self.user_session = data["userSession"]
                self.headers = {"Authorization": f"Bearer {self.user_session}"}
            else:
                raise Exception(f"Authentication failed: {data}")

        def get_session(self):
            return self.user_session
        
        def get_profile(self):
            url = f"{BASE_URL}/open-api/od/v1/profile"
            res = requests.get(url, headers=self.headers)
            return self._handle_response(res, "Profile")
        
        def get_holdings(self):
            url = f"{BASE_URL}/open-api/od/v1/holdings/CNC"
            res = requests.get(url, headers=self.headers)
            return self._handle_response(res, "Holdings")
        
        def get_positions(self):
            url = f"{BASE_URL}/open-api/od/v1/positions"
            res = requests.get(url, headers=self.headers)
            return self._handle_response(res, "Positions")
        
        def get_order_book(self):
            url = f"{BASE_URL}/open-api/od/v1/orders/book"
            res = requests.get(url, headers=self.headers)
            return self._handle_response(res, "Order Book")
        
        def get_trade_book(self):
            url = f"{BASE_URL}/open-api/od/v1/orders/trades"
            res = requests.get(url, headers=self.headers)
            return self._handle_response(res, "Trade Book")
        
        def get_limits(self):
            url = f"{BASE_URL}/open-api/od/v1/limits"
            res = requests.get(url, headers=self.headers)
            return self._handle_response(res, "Limits")

        def _handle_response(self, response, operation_name):
            if response.status_code != 200:
                raise Exception(f"{operation_name} Error {response.status_code}: {response.text}")
            try:
                return response.json()
            except Exception:
                raise Exception(f"Non-JSON response: {response.text}")

    def get_alice_client(ctx: Context):
        """Get or create AliceBlue client using session config"""
        if hasattr(ctx.session_state, 'alice_client'):
            return ctx.session_state.alice_client

        # Access session-specific config through context
        config = ctx.session_config
        
        alice = AliceBlue(
            user_id=config.user_id,
            auth_code=config.auth_code, 
            api_secret=config.api_secret
        )
        ctx.session_state.alice_client = alice
        return alice

    # Add tools
    @server.tool()
    def check_auth(ctx: Context) -> str:
        """Check authentication status"""
        try:
            alice = get_alice_client(ctx)
            session_id = alice.get_session()
            return f"✅ Authentication successful! Session ID: {session_id}"
        except Exception as e:
            return f"❌ Authentication failed: {str(e)}"

    @server.tool()
    def get_profile(ctx: Context) -> str:
        """Get user profile details"""
        try:
            alice = get_alice_client(ctx)
            data = alice.get_profile()
            return f"Profile data: {data}"
        except Exception as e:
            return f"Error getting profile: {str(e)}"

    @server.tool()
    def get_holdings(ctx: Context) -> str:
        """Get current stock holdings"""
        try:
            alice = get_alice_client(ctx)
            data = alice.get_holdings()
            return f"Holdings data: {data}"
        except Exception as e:
            return f"Error getting holdings: {str(e)}"

    @server.tool()
    def get_positions(ctx: Context) -> str:
        """Get current trading positions"""
        try:
            alice = get_alice_client(ctx)
            data = alice.get_positions()
            return f"Positions data: {data}"
        except Exception as e:
            return f"Error getting positions: {str(e)}"

    @server.tool()
    def get_order_book(ctx: Context) -> str:
        """Get order book"""
        try:
            alice = get_alice_client(ctx)
            data = alice.get_order_book()
            return f"Order book: {data}"
        except Exception as e:
            return f"Error getting order book: {str(e)}"

    @server.tool()
    def get_trade_book(ctx: Context) -> str:
        """Get trade book"""
        try:
            alice = get_alice_client(ctx)
            data = alice.get_trade_book()
            return f"Trade book: {data}"
        except Exception as e:
            return f"Error getting trade book: {str(e)}"

    @server.tool()
    def get_limits(ctx: Context) -> str:
        """Get account limits and margins"""
        try:
            alice = get_alice_client(ctx)
            data = alice.get_limits()
            return f"Account limits: {data}"
        except Exception as e:
            return f"Error getting limits: {str(e)}"

    return server