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

        def authenticate(self):
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
                    return True
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

        def _make_request(self, method, url, **kwargs):
            """Generic request handler with retry logic"""
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    # Ensure headers are set
                    if self.headers is None:
                        self.authenticate()
                    
                    # Add timeout if not specified
                    if 'timeout' not in kwargs:
                        kwargs['timeout'] = 15
                    
                    # Make the request
                    response = requests.request(method, url, **kwargs)
                    
                    # Check if session expired
                    if response.status_code == 401:
                        if attempt < max_retries - 1:
                            self.authenticate()  # Re-authenticate
                            if 'headers' in kwargs:
                                kwargs['headers'] = self.headers
                            continue
                        else:
                            raise Exception("Session expired and re-authentication failed")
                    
                    return response
                    
                except requests.exceptions.ConnectionError:
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    else:
                        raise Exception("Connection error: Unable to reach AliceBlue API")
                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    else:
                        raise Exception("Request timeout: AliceBlue API is not responding")
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    else:
                        raise e
            
            raise Exception("Max retries exceeded")

        def get_session(self):
            """Get current session ID"""
            return self.user_session
        
        def get_profile(self):
            """Get user profile"""
            url = f"{BASE_URL}/open-api/od/v1/profile"
            response = self._make_request("GET", url, headers=self.headers)
            
            if response.status_code != 200:
                raise Exception(f"Profile Error {response.status_code}: {response.text}")
            
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")
        
        def get_holdings(self):
            """Get user holdings"""
            url = f"{BASE_URL}/open-api/od/v1/holdings/CNC"
            response = self._make_request("GET", url, headers=self.headers)
            
            if response.status_code != 200:
                raise Exception(f"Holding Error {response.status_code}: {response.text}")
            
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")
        
        def get_positions(self):
            """Get user positions"""
            url = f"{BASE_URL}/open-api/od/v1/positions"
            response = self._make_request("GET", url, headers=self.headers)
            
            if response.status_code != 200:
                raise Exception(f"Position Error {response.status_code}: {response.text}")
            
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")
        
        def get_positions_sqroff(self, exch, symbol, qty, product, transaction_type):
            """Square off positions"""
            url = f"{BASE_URL}/open-api/od/v1/orders/positions/sqroff"
            payload = {
                "exch": exch,
                "symbol": symbol,
                "qty": qty,
                "product": product,
                "transaction_type": transaction_type
            }
            response = self._make_request("POST", url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"Position Square Off Error {response.status_code}: {response.text}")
            
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")

        def get_position_conversion(self, exchange, validity, prevProduct, product, quantity, tradingSymbol, transactionType, orderSource):
            """Position conversion"""
            url = f"{BASE_URL}/open-api/od/v1/conversion"
            payload = {
                "exchange": exchange,
                "validity": validity,
                "prevProduct": prevProduct,
                "product": product,
                "quantity": quantity,
                "tradingSymbol": tradingSymbol,
                "transactionType": transactionType,
                "orderSource": orderSource
            }
            response = self._make_request("POST", url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"Position Conversion Error {response.status_code}: {response.text}")
            
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")
        
        def get_place_order(self, instrument_id: str, exchange: str, transaction_type: str, quantity: int, order_type: str, product: str,
                        order_complexity: str, price: float, validity: str, sl_leg_price: Optional[float] = None,
                        target_leg_price: Optional[float] = None, sl_trigger_price: Optional[float] = None, trailing_sl_amount: Optional[float] = None,
                        disclosed_quantity: int = 0, source: str = "API"):
            """Place an order with Alice Blue API."""
            url = f"{BASE_URL}/open-api/od/v1/orders/placeorder"

            payload = [{
                "instrumentId": instrument_id,
                "exchange": exchange,
                "transactionType": transaction_type.upper(),
                "quantity": quantity,
                "orderType": order_type.upper(),
                "product": product.upper(),
                "orderComplexity": order_complexity.upper(),
                "price": price,
                "validity": validity.upper(),
                "disclosedQuantity": disclosed_quantity,
                "source": source.upper()
            }]

            if sl_leg_price is not None:
                payload[0]["slLegPrice"] = sl_leg_price
            if target_leg_price is not None:
                payload[0]["targetLegPrice"] = target_leg_price
            if sl_trigger_price is not None:
                payload[0]["slTriggerPrice"] = sl_trigger_price
            if trailing_sl_amount is not None:
                payload[0]["trailingSlAmount"] = trailing_sl_amount

            response = self._make_request("POST", url, headers=self.headers, json=payload)

            if response.status_code != 200:
                raise Exception(f"Order Place Error {response.status_code}: {response.text}")
            
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")
        
        def get_order_book(self):
            """Get order book"""
            url = f"{BASE_URL}/open-api/od/v1/orders/book"
            response = self._make_request("GET", url, headers=self.headers)
            
            if response.status_code != 200:
                raise Exception(f"Order Book Error {response.status_code}: {response.text}")
            
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")
        
        def get_order_history(self, brokerOrderId: str):
            """Get order history"""
            url = f"{BASE_URL}/open-api/od/v1/orders/history"
            payload = {"brokerOrderId": brokerOrderId}
            response = self._make_request("POST", url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"Order History Error {response.status_code}: {response.text}")
            
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")
        
        def get_modify_order(self, brokerOrderId: str, validity: str, quantity: Optional[int] = None, 
                            price: Optional[Union[int, float]] = None, triggerPrice: Optional[float] = None):
            """Modify order"""
            url = f"{BASE_URL}/open-api/od/v1/orders/modify"
            payload = [{
                "brokerOrderId": brokerOrderId,
                "quantity": quantity if quantity else "",
                "price": price if price else "",
                "triggerPrice": triggerPrice if triggerPrice else "",
                "validity": validity.upper()
            }]
            response = self._make_request("POST", url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"Order Modify Error {response.status_code}: {response.text}")

            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")
        
        def get_cancel_order(self, brokerOrderId: str):
            """Cancel an order"""
            url = f"{BASE_URL}/open-api/od/v1/orders/cancel"
            payload = {"brokerOrderId": brokerOrderId}
            response = self._make_request("POST", url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"Order Cancel Error {response.status_code}: {response.text}")
            
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")
        
        def get_trade_book(self):
            """Get trade book"""
            url = f"{BASE_URL}/open-api/od/v1/orders/trades"
            response = self._make_request("GET", url, headers=self.headers)
            
            if response.status_code != 200:
                raise Exception(f"Trade Book Error {response.status_code}: {response.text}")
            
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")
        
        def get_order_margin(self, exchange: str, instrumentId: str, transactionType: str, quantity: int, product: str, 
                            orderComplexity: str, orderType: str, validity: str, price: float = 0.0, 
                            slTriggerPrice: Optional[Union[int, float]] = None):
            """Check order margin"""
            url = f"{BASE_URL}/open-api/od/v1/orders/checkMargin"
            payload = [{
                "exchange": exchange.upper(),
                "instrumentId": instrumentId.upper(),
                "transactionType": transactionType.upper(),
                "quantity": quantity,
                "product": product.upper(),
                "orderComplexity": orderComplexity.upper(),
                "orderType": orderType.upper(),
                "price": price,
                "validity": validity.upper(),
                "slTriggerPrice": slTriggerPrice if slTriggerPrice is not None else ""
            }]
            response = self._make_request("POST", url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"Order Margin Error {response.status_code}: {response.text}")
            
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")
        
        def get_exit_bracket_order(self, brokerOrderId: str, orderComplexity: str):
            """Exit bracket order"""
            url = f"{BASE_URL}/open-api/od/v1/orders/exit/sno"
            payload = [{
                "brokerOrderId": brokerOrderId,
                "orderComplexity": orderComplexity.upper()
            }]
            response = self._make_request("POST", url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"Exit Bracket Order Error {response.status_code}: {response.text}")
            
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")
        
        def get_place_gtt_order(self, tradingSymbol: str, exchange: str, transactionType: str, orderType: str,
                                product: str, validity: str, quantity: int, price: float, orderComplexity: str, 
                                instrumentId: str, gttType: str, gttValue: float):
            """Place GTT order"""
            url = f"{BASE_URL}/open-api/od/v1/orders/gtt/execute"
            
            payload = {
                "tradingSymbol": tradingSymbol.upper(),
                "exchange": exchange.upper(),
                "transactionType": transactionType.upper(),
                "orderType": orderType.upper(),
                "product": product.upper(),
                "validity": validity.upper(),
                "quantity": quantity, 
                "price": price, 
                "orderComplexity": orderComplexity.upper(),
                "instrumentId": instrumentId,
                "gttType": gttType.upper(),
                "gttValue": gttValue 
            }
            
            try:
                response = self._make_request("POST", url, headers=self.headers, json=payload)
                return response.json()
            except requests.exceptions.HTTPError as e:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message") or error_data.get("emsg") or response.text
                except:
                    error_msg = response.text
                raise Exception(f"GTT Order Place Error {response.status_code}: {error_msg}")
            except requests.exceptions.RequestException as e:
                raise Exception(f"Network error: {str(e)}")
        
        def get_gtt_order_book(self):
            """Get GTT order book"""
            url = f"{BASE_URL}/open-api/od/v1/orders/gtt/orderbook"
            response = self._make_request("GET", url, headers=self.headers)
            
            if response.status_code != 200:
                raise Exception(f"GTT Order Book Error {response.status_code}: {response.text}")
            
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")
        
        def get_modify_gtt_order(self, brokerOrderId: str, instrumentId: str, tradingSymbol: str, 
                                exchange: str, orderType: str, product: str, validity: str, 
                                quantity: int, price: float, orderComplexity: str, 
                                gttType: str, gttValue: float):
            """Modify GTT order"""
            url = f"{BASE_URL}/open-api/od/v1/orders/gtt/modify"
            
            payload = {
                "brokerOrderId": brokerOrderId,
                "instrumentId": instrumentId,
                "tradingSymbol": tradingSymbol.upper(),
                "exchange": exchange.upper(),
                "orderType": orderType.upper(),
                "product": product.upper(),
                "validity": validity.upper(),
                "quantity": quantity,
                "price": price,
                "orderComplexity": orderComplexity.upper(),
                "gttType": gttType.upper(),
                "gttValue": gttValue
            }
            
            try:
                response = self._make_request("POST", url, headers=self.headers, json=payload)
                return response.json()
            except requests.exceptions.HTTPError as e:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message") or error_data.get("emsg") or response.text
                except:
                    error_msg = response.text
                raise Exception(f"GTT Modify Order Error {response.status_code}: {error_msg}")
            except requests.exceptions.RequestException as e:
                raise Exception(f"Network error: {str(e)}")
        
        def get_cancel_gtt_order(self, brokerOrderId: str):
            """Cancel GTT order"""
            url = f"{BASE_URL}/open-api/od/v1/orders/gtt/cancel"
            payload = {"brokerOrderId": brokerOrderId}
            response = self._make_request("POST", url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"GTT Cancel Order Error {response.status_code}: {response.text}")
            
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")
        
        def get_limits(self):
            """Get account limits"""
            url = f"{BASE_URL}/open-api/od/v1/limits"
            response = self._make_request("GET", url, headers=self.headers)
            
            if response.status_code != 200:
                raise Exception(f"Limits Error {response.status_code}: {response.text}")
            
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")

        def test_connection(self):
            """Test connection to AliceBlue API"""
            try:
                # Test authentication first
                if self.authenticate():
                    # Test with a simple profile API call
                    profile_data = self.get_profile()
                    return {
                        "status": "success",
                        "message": "Successfully connected to AliceBlue API",
                        "session_active": True,
                        "user_id": self.user_id,
                        "session_id": self.user_session
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Authentication failed",
                        "session_active": False
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Connection test failed: {str(e)}",
                    "session_active": False
                }

    def get_alice_client(ctx: Context):
        """Get or create AliceBlue client using session config"""
        if hasattr(ctx.session_state, 'alice_client'):
            # Test if existing client is still valid
            try:
                client = ctx.session_state.alice_client
                # Quick connection test
                client.get_profile()
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
        # Authenticate immediately
        alice.authenticate()
        ctx.session_state.alice_client = alice
        return alice

    # Add tools
    @server.tool()
    def test_connection(ctx: Context) -> dict:
        """Test connection to AliceBlue API and verify authentication"""
        try:
            alice = get_alice_client(ctx)
            return alice.test_connection()
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection test failed: {str(e)}",
                "session_active": False
            }

    @server.tool()
    def check_and_authenticate(ctx: Context) -> dict:
        """Check if AliceBlue session is active and re-authenticate if needed."""
        try:
            alice = get_alice_client(ctx)
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
    def get_profile(ctx: Context) -> dict:
        """Fetches the user's profile details."""
        try:
            alice = get_alice_client(ctx)
            return {"status": "success", "data": alice.get_profile()}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_holdings(ctx: Context) -> dict:
        """Fetches the user's Holdings Stock"""
        try:
            alice = get_alice_client(ctx)
            return {"status": "success", "data": alice.get_holdings()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
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

    return servernew