import os
import requests
import hashlib
from fastmcp import FastMCP
from typing import Optional, Union

BASE_URL = "https://a3.aliceblueonline.com"

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

# Initialize MCP server
mcp = FastMCP("AliceBlue Trading MCP")

# Global cached client
_alice_client = None

def get_alice_client() -> AliceBlue:
    """Return a cached AliceBlue client"""
    global _alice_client

    if _alice_client:
        return _alice_client

    user_id = os.getenv("ALICE_USER_ID")
    auth_code = os.getenv("ALICE_AUTH_CODE")
    api_secret = os.getenv("ALICE_API_SECRET")

    if not user_id or not auth_code or not api_secret:
        raise Exception("Missing credentials. Please set ALICE_USER_ID, ALICE_AUTH_CODE, and ALICE_API_SECRET")

    alice = AliceBlue(user_id=user_id, auth_code=auth_code, api_secret=api_secret)
    _alice_client = alice
    return _alice_client

@mcp.tool()
def check_authentication() -> dict:
    """Check if AliceBlue session is active"""
    try:
        alice = get_alice_client()
        session_id = alice.get_session()
        return {
            "status": "success",
            "authenticated": True,
            "session_id": session_id,
            "message": "Session is active"
        }
    except Exception as e:
        return {"status": "error", "authenticated": False, "message": str(e)}

@mcp.tool()
def get_user_profile() -> dict:
    """Get user profile details"""
    try:
        alice = get_alice_client()
        profile_data = alice.get_profile()
        return {"status": "success", "data": profile_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_stock_holdings() -> dict:
    """Get current stock holdings"""
    try:
        alice = get_alice_client()
        holdings_data = alice.get_holdings()
        return {"status": "success", "data": holdings_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_trading_positions() -> dict:
    """Get current trading positions"""
    try:
        alice = get_alice_client()
        positions_data = alice.get_positions()
        return {"status": "success", "data": positions_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_order_book() -> dict:
    """Get order book"""
    try:
        alice = get_alice_client()
        order_data = alice.get_order_book()
        return {"status": "success", "data": order_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_trade_book() -> dict:
    """Get trade book"""
    try:
        alice = get_alice_client()
        trade_data = alice.get_trade_book()
        return {"status": "success", "data": trade_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_account_limits() -> dict:
    """Get account limits and margins"""
    try:
        alice = get_alice_client()
        limits_data = alice.get_limits()
        return {"status": "success", "data": limits_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    mcp.run()