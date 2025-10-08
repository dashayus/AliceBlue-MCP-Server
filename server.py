import os
import json
import requests
import hashlib
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, EmbeddedResource
import pydantic

BASE_URL = "https://a3.aliceblueonline.com"

app = Server("aliceblue-trading")

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

@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="check_auth",
            description="Check authentication status",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_profile",
            description="Get user profile",
            inputSchema={
                "type": "object", 
                "properties": {}
            }
        ),
        Tool(
            name="get_holdings",
            description="Get stock holdings",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "check_auth":
        try:
            alice = get_alice_client()
            return [TextContent(type="text", text=json.dumps({
                "status": "success", 
                "session": alice.user_session
            }, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({
                "status": "error", 
                "message": str(e)
            }, indent=2))]
    
    elif name == "get_profile":
        try:
            alice = get_alice_client()
            data = alice.get_profile()
            return [TextContent(type="text", text=json.dumps({
                "status": "success", 
                "data": data
            }, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({
                "status": "error", 
                "message": str(e)
            }, indent=2))]
    
    elif name == "get_holdings":
        try:
            alice = get_alice_client()
            data = alice.get_holdings()
            return [TextContent(type="text", text=json.dumps({
                "status": "success", 
                "data": data
            }, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({
                "status": "error", 
                "message": str(e)
            }, indent=2))]
    
    else:
        return [TextContent(type="text", text=json.dumps({
            "status": "error", 
            "message": f"Unknown tool: {name}"
        }, indent=2))]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream=read_stream,
            write_stream=write_stream,
            initialization_options={}
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())