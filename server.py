import json
import hashlib
import requests
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("AliceBlue Trading MCP")

# AliceBlue configuration
BASE_URL = "https://ant.aliceblueonline.com"

def get_auth_headers(user_session: str):
    """Get authentication headers for API calls"""
    return {"Authorization": f"Bearer {user_session}", "Content-Type": "application/json"}

@mcp.tool()
def get_login_url(app_code: str, redirect_url: str = "https://smithery.ai/callback") -> str:
    """Get AliceBlue login URL for authentication
    
    Args:
        app_code: Your AliceBlue APP_CODE
        redirect_url: Redirect URL after login
    
    Returns:
        str: Login URL and instructions
    """
    login_url = f"{BASE_URL}/?appcode={app_code}&redirect_url={redirect_url}"
    
    return f"""
## 🔗 AliceBlue Login URL

Open this URL in your browser to start authentication:
{login_url}

## 📝 Instructions:
1. Open the above URL
2. Login with your AliceBlue credentials
3. After login, copy the 'userId' and 'authCode' from the redirect URL
4. Use these with generate_checksum tool
"""

@mcp.tool()
def generate_checksum(user_id: str, auth_code: str, api_secret: str) -> dict:
    """Generate checksum for AliceBlue authentication
    
    Args:
        user_id: User ID from login redirect
        auth_code: Authorization code from login redirect  
        api_secret: Your AliceBlue API_SECRET
    
    Returns:
        dict: Generated checksum and user info
    """
    try:
        # Generate checksum
        checksum_input = f"{user_id}{auth_code}{api_secret}"
        checksum = hashlib.sha256(checksum_input.encode()).hexdigest()
        
        return {
            "status": "success",
            "checksum": checksum,
            "user_id": user_id,
            "message": "Checksum generated successfully. Use complete_login with this checksum."
        }
    except Exception as e:
        return {"status": "error", "message": f"Checksum generation failed: {str(e)}"}

@mcp.tool()
def complete_login(checksum: str, user_id: str) -> dict:
    """Complete AliceBlue login process
    
    Args:
        checksum: Generated checksum from generate_checksum
        user_id: Your AliceBlue user ID
    
    Returns:
        dict: Login status and session tokens
    """
    try:
        url = f"{BASE_URL}/open-api/od/v1/vendor/getUserDetails"
        payload = {"checkSum": checksum}
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        if data.get("stat") == "Ok":
            return {
                "status": "success",
                "user_session": data.get("userSession"),
                "client_id": data.get("clientId"),
                "message": "Login successful! Save user_session for future API calls."
            }
        else:
            return {"status": "error", "message": f"Login failed: {data}"}
            
    except Exception as e:
        return {"status": "error", "message": f"Login failed: {str(e)}"}

@mcp.tool()
def get_profile(user_session: str) -> dict:
    """Get user profile information
    
    Args:
        user_session: User session token from complete_login
    """
    try:
        url = f"{BASE_URL}/open-api/od/v1/profile"
        headers = get_auth_headers(user_session)
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"Failed to get profile: {str(e)}"}

@mcp.tool()
def get_holdings(user_session: str, product_type: str = "CNC") -> dict:
    """Get current stock holdings
    
    Args:
        user_session: User session token from complete_login
        product_type: Product type (CNC, MIS, NRML)
    """
    try:
        url = f"{BASE_URL}/open-api/od/v1/holdings/{product_type}"
        headers = get_auth_headers(user_session)
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"Failed to get holdings: {str(e)}"}

@mcp.tool()
def get_positions(user_session: str) -> dict:
    """Get current trading positions
    
    Args:
        user_session: User session token from complete_login
    """
    try:
        url = f"{BASE_URL}/open-api/od/v1/positions"
        headers = get_auth_headers(user_session)
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"Failed to get positions: {str(e)}"}

@mcp.tool()
def get_order_book(user_session: str) -> dict:
    """Get order book
    
    Args:
        user_session: User session token from complete_login
    """
    try:
        url = f"{BASE_URL}/open-api/od/v1/orders"
        headers = get_auth_headers(user_session)
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"Failed to get order book: {str(e)}"}

@mcp.tool()
def get_margins(user_session: str) -> dict:
    """Get account margins
    
    Args:
        user_session: User session token from complete_login
    """
    try:
        url = f"{BASE_URL}/open-api/od/v1/margins"
        headers = get_auth_headers(user_session)
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"Failed to get margins: {str(e)}"}

if __name__ == "__main__":
    mcp.run()