from mcp.server.fastmcp import FastMCP
import requests
import hashlib
import uvicorn
import os

BASE_URL = "https://a3.aliceblueonline.com"

# Create server
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

@server.tool()
def check_auth(user_id: str, auth_code: str, api_secret: str) -> str:
    """Check authentication status"""
    try:
        alice = AliceBlue(user_id, auth_code, api_secret)
        session_id = alice.user_session
        return f"✅ Authentication successful! Session ID: {session_id}"
    except Exception as e:
        return f"❌ Authentication failed: {str(e)}"

@server.tool()
def get_profile(user_id: str, auth_code: str, api_secret: str) -> str:
    """Get user profile details"""
    try:
        alice = AliceBlue(user_id, auth_code, api_secret)
        data = alice.get_profile()
        return f"Profile data: {data}"
    except Exception as e:
        return f"Error getting profile: {str(e)}"

@server.tool()
def get_holdings(user_id: str, auth_code: str, api_secret: str) -> str:
    """Get current stock holdings"""
    try:
        alice = AliceBlue(user_id, auth_code, api_secret)
        data = alice.get_holdings()
        return f"Holdings data: {data}"
    except Exception as e:
        return f"Error getting holdings: {str(e)}"

@server.tool()
def get_positions(user_id: str, auth_code: str, api_secret: str) -> str:
    """Get current trading positions"""
    try:
        alice = AliceBlue(user_id, auth_code, api_secret)
        data = alice.get_positions()
        return f"Positions data: {data}"
    except Exception as e:
        return f"Error getting positions: {str(e)}"

@server.tool()
def get_order_book(user_id: str, auth_code: str, api_secret: str) -> str:
    """Get order book"""
    try:
        alice = AliceBlue(user_id, auth_code, api_secret)
        data = alice.get_order_book()
        return f"Order book: {data}"
    except Exception as e:
        return f"Error getting order book: {str(e)}"

@server.tool()
def get_trade_book(user_id: str, auth_code: str, api_secret: str) -> str:
    """Get trade book"""
    try:
        alice = AliceBlue(user_id, auth_code, api_secret)
        data = alice.get_trade_book()
        return f"Trade book: {data}"
    except Exception as e:
        return f"Error getting trade book: {str(e)}"

@server.tool()
def get_limits(user_id: str, auth_code: str, api_secret: str) -> str:
    """Get account limits and margins"""
    try:
        alice = AliceBlue(user_id, auth_code, api_secret)
        data = alice.get_limits()
        return f"Account limits: {data}"
    except Exception as e:
        return f"Error getting limits: {str(e)}"

# Get the FastAPI app
app = server.app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)