import os
import requests
import hashlib
from fastmcp import FastMCP

BASE_URL = "https://a3.aliceblueonline.com"

mcp = FastMCP("AliceBlue Trading")

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

    def _handle_response(self, response, operation_name):
        if response.status_code != 200:
            raise Exception(f"{operation_name} Error {response.status_code}: {response.text}")
        try:
            return response.json()
        except Exception:
            raise Exception(f"Non-JSON response: {response.text}")

# Global cached client
_alice_client = None

def get_alice_client():
    global _alice_client
    if _alice_client:
        return _alice_client

    user_id = os.getenv("ALICE_USER_ID")
    auth_code = os.getenv("ALICE_AUTH_CODE")
    api_secret = os.getenv("ALICE_API_SECRET")

    if not user_id or not auth_code or not api_secret:
        raise Exception("Missing credentials")

    alice = AliceBlue(user_id=user_id, auth_code=auth_code, api_secret=api_secret)
    _alice_client = alice
    return _alice_client

@mcp.tool()
def check_auth() -> dict:
    """Check authentication status"""
    try:
        alice = get_alice_client()
        return {"status": "success", "session": alice.user_session}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_profile() -> dict:
    """Get user profile"""
    try:
        alice = get_alice_client()
        data = alice.get_profile()
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_holdings() -> dict:
    """Get stock holdings"""
    try:
        alice = get_alice_client()
        data = alice.get_holdings()
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    mcp.run()