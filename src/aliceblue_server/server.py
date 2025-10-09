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

# CORRECTED BASE URL - Use "ant" instead of "a3"
BASE_URL = "https://ant.aliceblueonline.com"

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
            self.last_authentication = None

        async def initialize(self):
            """Initialize the client with authentication"""
            await self.authenticate()

        async def _make_request(self, method, url, **kwargs):
            """Generic request handler with retry logic"""
            max_retries = 2  # Reduced retries
            for attempt in range(max_retries):
                try:
                    # Ensure headers are set
                    if self.headers is None:
                        await self.authenticate()
                    
                    # Add shorter timeout if not specified
                    if 'timeout' not in kwargs:
                        kwargs['timeout'] = 15  # Reduced timeout
                    
                    # Make the request
                    response = requests.request(method, url, **kwargs)
                    
                    # Check if session expired
                    if response.status_code == 401:
                        if attempt < max_retries - 1:
                            await self.authenticate()  # Re-authenticate
                            if 'headers' in kwargs:
                                kwargs['headers'] = self.headers
                            continue
                        else:
                            raise Exception("Session expired and re-authentication failed")
                    
                    return response
                    
                except requests.exceptions.ConnectionError:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)  # Wait before retry
                        continue
                    else:
                        raise Exception("Connection error: Unable to reach AliceBlue API")
                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                        continue
                    else:
                        raise Exception("Request timeout: AliceBlue API is not responding")
                except Exception as e:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                        continue
                    else:
                        raise e
            
            raise Exception("Max retries exceeded")

        async def authenticate(self):
            """Authenticate with AliceBlue API"""
            try:
                # Prepare checksum - using the exact format from documentation
                raw_string = f"{self.user_id}{self.auth_code}{self.api_secret}"
                checksum = hashlib.sha256(raw_string.encode()).hexdigest()

                # API request - using correct endpoint
                url = f"{BASE_URL}/open-api/od/v1/vendor/getUserDetails"
                payload = {"checkSum": checksum} 

                # Use shorter timeout for authentication
                response = requests.post(url, json=payload, timeout=10)
                
                # Handle API response
                if response.status_code != 200:
                    raise Exception(f"API Error {response.status_code}: {response.text}")

                data = response.json()
                if data.get("stat") == "Ok":
                    self.user_session = data["userSession"]
                    self.headers = {
                        "Authorization": f"Bearer {self.user_session}",
                        "Content-Type": "application/json"
                    }
                    self.last_authentication = time.time()
                    print(f"✅ Authenticated successfully. Session: {self.user_session}")
                else:
                    error_msg = data.get("message", "Unknown authentication error")
                    raise Exception(f"Authentication failed: {error_msg}")
                    
            except requests.exceptions.ConnectionError:
                raise Exception("Cannot connect to AliceBlue API. Check your internet connection and try again.")
            except requests.exceptions.Timeout:
                raise Exception("AliceBlue API timeout. Please try again later.")
            except json.JSONDecodeError:
                raise Exception(f"Invalid JSON response from API: {response.text}")
            except Exception as e:
                raise Exception(f"Authentication error: {str(e)}")

        def get_session(self):
            """Get current session ID"""
            return self.user_session
        
        async def get_profile(self):
            """Get user profile"""
            url = f"{BASE_URL}/open-api/od/v1/profile"
            response = await self._make_request("GET", url, headers=self.headers)
            
            if response.status_code != 200:
                raise Exception(f"Profile Error {response.status_code}: {response.text}")
            
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")
        
        async def get_holdings(self):
            """Get user holdings"""
            url = f"{BASE_URL}/open-api/od/v1/holdings/CNC"
            response = await self._make_request("GET", url, headers=self.headers)
            
            if response.status_code != 200:
                raise Exception(f"Holding Error {response.status_code}: {response.text}")
            
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")
        
        async def get_positions(self):
            """Get user positions"""
            url = f"{BASE_URL}/open-api/od/v1/positions"
            response = await self._make_request("GET", url, headers=self.headers)
            
            if response.status_code != 200:
                raise Exception(f"Position Error {response.status_code}: {response.text}")
            
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")

        # ... (other methods follow the same async pattern)

        async def test_connection(self):
            """Test connection to AliceBlue API"""
            try:
                # Test with a simple profile API call
                profile_data = await self.get_profile()
                return {
                    "status": "success",
                    "message": "Successfully connected to AliceBlue API",
                    "session_active": True,
                    "user_id": self.user_id,
                    "session_id": self.user_session
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Connection test failed: {str(e)}",
                    "session_active": False
                }

    async def get_alice_client(ctx: Context):
        """Get or create AliceBlue client using session config"""
        if hasattr(ctx.session_state, 'alice_client'):
            # Test if existing client is still valid
            try:
                client = ctx.session_state.alice_client
                # Quick connection test
                await client.get_profile()
                return client
            except:
                # Re-authenticate if client is invalid
                pass

        # Access session-specific config through context
        config = ctx.session_config
        
        alice = AliceBlue(
            user_id=config.user_id,
            auth_code=config.auth_code, 
            api_secret=config.api_secret
        )
        await alice.initialize()  # Initialize with authentication
        ctx.session_state.alice_client = alice
        return alice

    # Add tools with async support
    @server.tool()
    async def test_connection(ctx: Context) -> dict:
        """Test connection to AliceBlue API and verify authentication"""
        try:
            alice = await get_alice_client(ctx)
            result = await alice.test_connection()
            return result
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection test failed: {str(e)}",
                "session_active": False
            }

    @server.tool()
    async def check_and_authenticate(ctx: Context) -> dict:
        """Check if AliceBlue session is active and re-authenticate if needed."""
        try:
            alice = await get_alice_client(ctx)
            session_id = alice.get_session()
            return {
                "status": "success",
                "authenticated": True,
                "session_id": session_id,
                "user_id": alice.user_id,
                "message": "Session is active and valid"
            }
        except Exception as e:
            return {"status": "error", "authenticated": False, "message": str(e)}

    @server.tool()
    async def get_profile(ctx: Context) -> dict:
        """Fetches the user's profile details."""
        try:
            alice = await get_alice_client(ctx)
            return {"status": "success", "data": await alice.get_profile()}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    async def get_holdings(ctx: Context) -> dict:
        """Fetches the user's Holdings Stock"""
        try:
            alice = await get_alice_client(ctx)
            return {"status": "success", "data": await alice.get_holdings()}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Add other tools following the same async pattern...
    
    @server.tool()
    def get_positions(ctx: Context) -> dict:
        """Fetches the user's Positions"""
        try:
            alice = get_alice_client(ctx)
            return{"status": "success", "data": alice.get_positions()}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_positions_sqroff(ctx: Context, exch: str, symbol: str, qty: str, product: str, 
                            transaction_type: str) -> dict:
        """Position Square Off"""
        try:
            alice = get_alice_client(ctx)
            return {
                "status":"success",
                "data": alice.get_positions_sqroff(
                    exch=exch,
                    symbol=symbol,
                    qty=qty,
                    product=product,
                    transaction_type=transaction_type
                )
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_position_conversion(ctx: Context, exchange: str, validity: str, prevProduct: str, product: str, quantity: int, 
                                tradingSymbol: str, transactionType: str, orderSource: str) -> dict:
        """Position conversion"""
        try:
            alice = get_alice_client(ctx)
            return{
                "status":"success",
                "data": alice.get_position_conversion(
                    exchange=exchange,
                    validity=validity,
                    prevProduct=prevProduct,
                    product=product,
                    quantity=quantity,
                    tradingSymbol=tradingSymbol,
                    transactionType=transactionType,
                    orderSource=orderSource
                )
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @server.tool()
    def place_order(ctx: Context, instrument_id: str, exchange: str, transaction_type: str, quantity: int, order_type: str, product: str,
                        order_complexity: str, price: float, validity: str) -> dict:
        """Places an order for the given stock."""
        try:
            alice = get_alice_client(ctx)
            return {
                "status": "success",
                "data": alice.get_place_order(
                    instrument_id = instrument_id,
                    exchange=exchange,
                    transaction_type=transaction_type,
                    quantity = quantity,
                    order_type = order_type,
                    product = product,
                    order_complexity = order_complexity,
                    price=price,
                    validity = validity
                )
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_order_book(ctx: Context) -> dict:
        """Fetches Order Book"""
        try:
            alice = get_alice_client(ctx)
            return {
                "status": "success",
                "data": alice.get_order_book()
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @server.tool()
    def get_order_history(ctx: Context, brokerOrderId: str) -> dict:
        """Fetchs Orders History"""
        try:
            alice = get_alice_client(ctx)
            return{
                "status": "success",
                "data": alice.get_order_history(
                    brokerOrderId=brokerOrderId
                )
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_modify_order(ctx: Context, brokerOrderId:str, validity: str , quantity: Optional[int] = None,
                        price: Optional[Union[int, float]] = None, triggerPrice: Optional[float] = None) -> dict:
        """Modify Order"""
        try:
            alice = get_alice_client(ctx)
            return {
                "status": "success",
                "data": alice.get_modify_order(
                    brokerOrderId = brokerOrderId,
                    quantity= quantity if quantity else "",
                    validity= validity,
                    price= price if price else "",
                    triggerPrice=triggerPrice if triggerPrice else ""
                )
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_cancel_order(ctx: Context, brokerOrderId: str) -> dict:
        """Cancel Order"""
        try:
            alice = get_alice_client(ctx)
            return {
                "status": "success",
                "data": alice.get_cancel_order(
                    brokerOrderId=brokerOrderId
                )
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_trade_book(ctx: Context) -> dict:
        """Fetches Trade Book"""
        try:
            alice = get_alice_client(ctx)
            return{
                "status": "success",
                "data": alice.get_trade_book()
            }
        except Exception as e:
            return {"status": "error", "message" : str(e)}

    @server.tool()
    def get_order_margin(ctx: Context, exchange:str, instrumentId:str, transactionType:str, quantity:int, product:str, 
                            orderComplexity:str, orderType:str, validity:str, price=0.0, 
                            slTriggerPrice: Optional[Union[int, float]] = None) -> dict:
        """Order Margin"""
        try:
            alice = get_alice_client(ctx)
            return{
                "status": "success",
                "data": alice.get_order_margin(
                    exchange=exchange,
                    instrumentId = instrumentId,
                    transactionType=transactionType,
                    quantity=quantity,
                    product=product,
                    orderComplexity=orderComplexity,
                    orderType=orderType,
                    validity=validity,
                    price=price,
                    slTriggerPrice= slTriggerPrice if slTriggerPrice is not None else ""
                )
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_exit_bracket_order(ctx: Context, brokerOrderId: str, orderComplexity:str) -> dict:
        """Exit Bracket Order"""
        try:
            alice = get_alice_client(ctx)
            return {
                "status": "success",
                "data": alice.get_exit_bracket_order(
                    brokerOrderId=brokerOrderId,
                    orderComplexity=orderComplexity
                )
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_place_gtt_order(ctx: Context, tradingSymbol: str, exchange: str, transactionType: str, orderType: str,
                                product: str, validity: str, quantity: int, price: float, orderComplexity: str, 
                                instrumentId: str, gttType: str, gttValue: float) -> dict:
        """Place GTT Order"""
        try:
            alice = get_alice_client(ctx)
            return {
                "status": "success",
                "data": alice.get_place_gtt_order(
                    tradingSymbol=tradingSymbol,
                    exchange=exchange,
                    transactionType=transactionType,
                    orderType=orderType,
                    product=product,
                    validity=validity,
                    quantity=quantity,
                    price=price,
                    orderComplexity=orderComplexity,
                    instrumentId = instrumentId,
                    gttType=gttType,
                    gttValue=gttValue
                )
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_gtt_order_book(ctx: Context) -> dict:
        """Fetches GTT Order Book"""
        try:
            alice = get_alice_client(ctx)
            return{
                "status": "success",
                "data": alice.get_gtt_order_book()
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_modify_gtt_order(ctx: Context, brokerOrderId: str, instrumentId: str, tradingSymbol: str, 
                                exchange: str, orderType: str, product: str, validity: str, 
                                quantity: int, price: float, orderComplexity: str, 
                                gttType: str, gttValue: float) -> dict:
        """Modify GTT Order"""
        try:
            alice = get_alice_client(ctx)
            return{
                "status": "success",
                "data": alice.get_modify_gtt_order(
                    brokerOrderId=brokerOrderId,
                    instrumentId = instrumentId,
                    tradingSymbol=tradingSymbol,
                    exchange=exchange,
                    orderType=orderType,
                    product=product,
                    validity=validity,
                    quantity=quantity,
                    price=price,
                    orderComplexity=orderComplexity,
                    gttType=gttType,
                    gttValue=gttValue,
                )
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_cancel_gtt_order(ctx: Context, brokerOrderId: str) -> dict:
        """Cancel GTT Order"""
        try:
            alice = get_alice_client(ctx)
            return{
                "status": "success",
                "data": alice.get_cancel_gtt_order(
                    brokerOrderId=brokerOrderId
                )
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_limits(ctx: Context) -> dict:
        """Get Account Limits"""
        try:
            alice = get_alice_client(ctx)
            return{
                "status": "success",
                "data": alice.get_limits()
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    return server