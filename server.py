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
        # Prepare checksum
        raw_string = f"{self.user_id}{self.auth_code}{self.api_secret}"
        checksum = hashlib.sha256(raw_string.encode()).hexdigest()

        # API request
        url = f"{BASE_URL}/open-api/od/v1/vendor/getUserDetails"
        payload = {"checkSum": checksum} 

        res = requests.post(url, json=payload)

        # Handle API response
        if res.status_code != 200:
            raise Exception(f"API Error: {res.text}")

        data = res.json()
        if data.get("stat") == "Ok":
            self.user_session = data["userSession"]
            self.headers = {
                "Authorization": f"Bearer {self.user_session}"
            }
            print("Authentication Successful")
        else:
            raise Exception(f"Authentication failed: {data}")

    def get_session(self):
        return self.user_session
    
    def get_profile(self):
        url = f"{BASE_URL}/open-api/od/v1/profile"
        res = requests.get(url, headers=self.headers)
        
        if res.status_code != 200:
            raise Exception(f"Profile Error {res.status_code}: {res.text}")
        try:
            return res.json()
        except Exception:
            raise Exception(f"Non-JSON response: {res.text}")
    
    def get_holdings(self):
        url = f"{BASE_URL}/open-api/od/v1/holdings/CNC"
        res = requests.get(url, headers=self.headers)
        
        if res.status_code != 200:
            raise Exception(f"Holding Error {res.status_code}: {res.text}")
        try:
            return res.json()
        except Exception:
            raise Exception(f"Non-JSON response: {res.text}")
    
    def get_positions(self):
        url = f"{BASE_URL}/open-api/od/v1/positions"
        res = requests.get(url, headers=self.headers)
        
        if res.status_code != 200:
            raise Exception(f"Position Error {res.status_code}: {res.text}")
        try:
            return res.json()
        except Exception:
            raise Exception(f"Non-JSON response: {res.text}")
    
    def get_positions_sqroff(self, exch, symbol, qty, product, transaction_type):
        url = f"{BASE_URL}/open-api/od/v1/orders/positions/sqroff"
        payload = {
            "exch": exch,
            "symbol": symbol,
            "qty": qty,
            "product": product,
            "transaction_type": transaction_type
        }
        res = requests.post(url, headers=self.headers, json=payload)
        
        if res.status_code != 200:
            raise Exception(f"Position Square Off Error {res.status_code}: {res.text}")
        try:
            return res.json()
        except Exception:
            raise Exception(f"Non-JSON response: {res.text}")

    def get_position_conversion(self, exchange, validity, prevProduct, product, quantity, tradingSymbol, transactionType,orderSource):
        url = f"{BASE_URL}/open-api/od/v1/conversion"
        payload = {
            "exchange": exchange,
            "validity": validity,
            "prevProduct": prevProduct,
            "product": product,
            "quantity": quantity,
            "tradingSymbol": tradingSymbol,
            "transactionType": transactionType,
            "orderSource":orderSource
        }
        res = requests.post(url, headers=self.headers, json=payload)
        
        if res.status_code != 200:
            raise Exception(f"Position Conversion Error {res.status_code}: {res.text}")
        try:
            return res.json()
        except Exception:
            raise Exception(f"Non-JSON response: {res.text}")
    
    def get_place_order(self,instrument_id: str, exchange: str, transaction_type: str, quantity: int, order_type: str, product: str,
                    order_complexity: str, price: float, validity: str, sl_leg_price: Optional[float] = None,
                    target_leg_price: Optional[float] = None, sl_trigger_price: Optional[float] = None, trailing_sl_amount: Optional[float] = None,
                    disclosed_quantity: int = 0,source: str = "API"):
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

        res = requests.post(url, headers=self.headers, json=payload)

        if res.status_code != 200:
            raise Exception(f"Order Place Error {res.status_code}: {res.text}")
        try:
            return res.json()
        except Exception:
            raise Exception(f"Non-JSON response: {res.text}")
    
    def get_order_book(self):
        url = f"{BASE_URL}/open-api/od/v1/orders/book"
        res = requests.get(url, headers=self.headers)
        
        if res.status_code != 200:
            raise Exception(f"Order Book Error {res.status_code}: {res.text}")
        try:
            return res.json()
        except Exception:
            raise Exception(f"Non-JSON response: {res.text}")
    
    def get_order_history(self, brokerOrderId: str):
        url = f"{BASE_URL}/open-api/od/v1/orders/history"
        payload = {"brokerOrderId": brokerOrderId}
        res = requests.post(url, headers=self.headers, json = payload)
        
        if res.status_code != 200:
            raise Exception(f"Order History Error {res.status_code}: {res.text}")
        try:
            return res.json()
        except Exception:
            raise Exception(f"Non-JSON response: {res.text}")
    
    def get_modify_order(self, brokerOrderId:str, validity: str , quantity: Optional[int] = None,price: Optional[Union[int, float]] = None, 
                         triggerPrice: Optional[float] = None
                         ):
        url = f"{BASE_URL}/open-api/od/v1/orders/modify"
        payload = [{
            "brokerOrderId": brokerOrderId,
            "quantity": quantity if quantity else "",
            "price": price if price else "",
            "triggerPrice": triggerPrice if triggerPrice else "",
            "validity": validity.upper()
        }]
        res = requests.post(url, headers=self.headers, json=payload)
        if res.status_code != 200:
            raise Exception(f"Order Modify Error {res.status_code}: {res.text}")

        try:
            return res.json()
        except Exception:
            raise Exception(f"Non-JSON response: {res.text}")
    
    def get_cancel_order(self, brokerOrderId):
        """Cancel an order."""
        url = f"{BASE_URL}/open-api/od/v1/orders/cancel"
        payload = {"brokerOrderId":brokerOrderId}
        res = requests.post(url, headers=self.headers, json=payload)
        
        if res.status_code != 200:
            raise Exception(f"Order Cancel Error {res.status_code}: {res.text}")
        try:
            return res.json()
        except Exception:
            raise Exception(f"Non-JSON response: {res.text}")
    
    def get_trade_book(self):
        url = f"{BASE_URL}/open-api/od/v1/orders/trades"
        res = requests.get(url, headers=self.headers)
        
        if res.status_code != 200:
            raise Exception(f"Order Cancel Error {res.status_code}: {res.text}")
        try:
            return res.json()
        except Exception:
            raise Exception(f"Non-JSON response: {res.text}")
    
    def get_order_margin(self, exchange:str, instrumentId:str, transactionType:str, quantity:int, product:str, 
                         orderComplexity:str, orderType:str, validity:str, price=0.0, slTriggerPrice: Optional[Union[int, float]] = None):
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
        res = requests.post(url, headers=self.headers, json=payload)
        
        if res.status_code != 200:
            raise Exception(f"Order Cancel Error {res.status_code}: {res.text}")
        try:
            return res.json()
        except Exception:
            raise Exception(f"Non-JSON response: {res.text}")
    
    def get_exit_bracket_order(self, brokerOrderId: str, orderComplexity: str):
        url = f"{BASE_URL}/open-api/od/v1/orders/exit/sno"
        payload = [{
            "brokerOrderId": brokerOrderId,
            "orderComplexity": orderComplexity.upper()
        }]
        res = requests.post(url, headers=self.headers, json=payload)
        
        if res.status_code != 200:
            raise Exception(f"Exit Bracket Order Error {res.status_code}: {res.text}")
        
        try:
            return res.json()
        except Exception:
            raise Exception(f"Non-JSON response: {res.text}")
    
    def get_place_gtt_order(self, tradingSymbol: str, exchange: str, transactionType: str, orderType: str,
                            product: str, validity: str, quantity: int, price: float, orderComplexity: str, 
                            instrumentId: str, gttType: str, gttValue: float):
        
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
            res = requests.post(url, headers=self.headers, json=payload)
            res.raise_for_status()
            return res.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_data = res.json()
                error_msg = error_data.get("message") or error_data.get("emsg") or res.text
            except:
                error_msg = res.text
            raise Exception(f"GTT Order Place Error {res.status_code}: {error_msg}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
    
    def get_gtt_order_book(self):
        url = f"{BASE_URL}/open-api/od/v1/orders/gtt/orderbook"
        res = requests.get(url, headers=self.headers)
        
        if res.status_code != 200:
            raise Exception(f"GTT Order Book Error {res.status_code}: {res.text}")
        
        try:
            return res.json()
        except Exception:
            raise Exception(f"Non-JSON response: {res.text}")
    
    def get_modify_gtt_order(self, brokerOrderId: str, instrumentId: str, tradingSymbol: str, 
                            exchange: str, orderType: str, product: str, validity: str, 
                            quantity: int, price: float, orderComplexity: str, 
                            gttType: str, gttValue: float):
        
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
            res = requests.post(url, headers=self.headers, json=payload)
            res.raise_for_status()
            return res.json()
            
        except requests.exceptions.HTTPError as e:
            try:
                error_data = res.json()
                error_msg = error_data.get("message") or error_data.get("emsg") or res.text
            except:
                error_msg = res.text
            raise Exception(f"GTT Modify Order Error {res.status_code}: {error_msg}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
    
    def get_cancel_gtt_order(self, brokerOrderId):
        url = f"{BASE_URL}/open-api/od/v1/orders/gtt/cancel"
        payload = {"brokerOrderId": brokerOrderId}
        res = requests.post(url, headers=self.headers, json=payload)
        
        if res.status_code != 200:
            raise Exception(f"GTT Cancel Order Error {res.status_code}: {res.text}")
        try:
            return res.json()
        except Exception:
            raise Exception(f"Non-JSON response: {res.text}")
    
    def get_limits(self):
        url = f"{BASE_URL}/open-api/od/v1/limits"
        res = requests.get(url, headers=self.headers)
        
        if res.status_code != 200:
            raise Exception(f"Exit Bracket Order Error {res.status_code}: {res.text}")   
        try:
            return res.json()
        except Exception:
            raise Exception(f"Non-JSON response: {res.text}")


mcp = FastMCP(
    name="AliceBlue Trading MCP",
    dependencies=["requests"]
)

# Global cached client
_alice_client = None


def get_alice_client(force_refresh: bool = False) -> AliceBlue:
    """Return a cached AliceBlue client, authenticate only once unless forced."""
    global _alice_client

    if _alice_client and not force_refresh:
        return _alice_client

    # Get credentials from environment variables (set by Smithery)
    user_id = os.getenv("ALICE_USER_ID")
    auth_code = os.getenv("ALICE_AUTH_CODE")
    api_secret = os.getenv("ALICE_API_SECRET")

    if not user_id or not auth_code or not api_secret:
        raise Exception("Missing credentials. Please set ALICE_USER_ID, ALICE_AUTH_CODE, and ALICE_API_SECRET in your Smithery configuration")

    alice = AliceBlue(user_id=user_id, auth_code=auth_code, api_secret=api_secret)
    _alice_client = alice
    return _alice_client


@mcp.tool()
def check_and_authenticate() -> dict:
    """Check if AliceBlue session is active."""
    global _alice_client
    try:
        if not _alice_client:
            return {
                "status": "error",
                "authenticated": False,
                "message": "No active session. Please run initiate_login first."
            }

        session_id = _alice_client.get_session()
        return {
            "status": "success",
            "authenticated": True,
            "session_id": session_id,
            "user_id": _alice_client.user_id,
            "message": "Session is active"
        }
    except Exception as e:
        return {"status": "error", "authenticated": False, "message": str(e)}


@mcp.tool()
def initiate_login(force_refresh: bool = False) -> dict:
    """Login and create a new AliceBlue session if none exists or forced."""
    try:
        alice = get_alice_client(force_refresh=force_refresh)
        return {
            "status": "success",
            "message": "Login successful! New session created" if force_refresh else "Session active",
            "session_id": alice.get_session(),
            "user_id": alice.user_id
        }
    except Exception as e:
        return {"status": "error", "message": f"Login failed: {e}"}


@mcp.tool()
def close_session() -> dict:
    """Explicitly close the current session (forces next call to re-authenticate)."""
    global _alice_client
    _alice_client = None
    return {"status": "success", "message": "Session closed. Next call will require re-authentication."}

@mcp.tool()
def get_profile() -> dict:
    """Fetches the user's profile details."""
    try:
        alice = get_alice_client()
        return {"status": "success", "data": alice.get_profile()}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def get_holdings() -> dict:
    """Fetches the user's Holdings Stock"""
    try:
        alice = get_alice_client()
        return {"status": "success", "data": alice.get_holdings()}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@mcp.tool()
def get_positions()-> dict:
    """Fetches the user's Positions"""
    try:
        alice = get_alice_client()
        return{"status": "success", "data": alice.get_positions()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_positions_sqroff(exch: str, symbol: str, qty: str, product: str, 
                         transaction_type: str)-> dict:
    """Position Square Off"""
    try:
        alice = get_alice_client()
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

@mcp.tool()
def get_position_conversion(exchange: str, validity: str, prevProduct: str, product: str, quantity: int, 
                            tradingSymbol: str, transactionType: str, orderSource: str)->dict:
    """Position conversion"""
    try:
        alice = get_alice_client()
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
    
@mcp.tool()
def place_order(instrument_id: str, exchange: str, transaction_type: str, quantity: int, order_type: str, product: str,
                    order_complexity: str, price: float, validity: str) -> dict:
    """Places an order for the given stock."""
    try:
        alice = get_alice_client()
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

@mcp.tool()
def get_order_book()-> dict:
    """Fetches Order Book"""
    try:
        alice = get_alice_client()
        return {
            "status": "success",
            "data": alice.get_order_book()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@mcp.tool()
def get_order_history(brokerOrderId: str)-> dict:
    """Fetchs Orders History"""
    try:
        alice = get_alice_client()
        return{
            "status": "success",
            "data": alice.get_order_history(
                brokerOrderId=brokerOrderId
            )
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_modify_order(brokerOrderId:str, validity: str , quantity: Optional[int] = None,
                     price: Optional[Union[int, float]] = None, triggerPrice: Optional[float] = None)-> dict:
    """Modify Order"""
    try:
        alice = get_alice_client()
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

@mcp.tool()
def get_cancel_order(brokerOrderId: str)-> dict:
    """Cancel Order"""
    try:
        alice = get_alice_client()
        return {
            "status": "success",
            "data": alice.get_cancel_order(
                brokerOrderId=brokerOrderId
            )
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_trade_book()-> dict:
    """Fetches Trade Book"""
    try:
        alice = get_alice_client()
        return{
            "status": "success",
            "data": alice.get_trade_book()
        }
    except Exception as e:
        return {"status": "error", "message" : str(e)}

@mcp.tool()
def get_order_margin(exchange:str, instrumentId:str, transactionType:str, quantity:int, product:str, 
                         orderComplexity:str, orderType:str, validity:str, price=0.0, 
                         slTriggerPrice: Optional[Union[int, float]] = None)-> dict:
    """Order Margin"""
    try:
        alice = get_alice_client()
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

@mcp.tool()
def get_exit_bracket_order(brokerOrderId: str, orderComplexity:str)->dict:
    """Exit Bracket Order"""
    try:
        alice = get_alice_client()
        return {
            "status": "success",
            "data": alice.get_exit_bracket_order(
                brokerOrderId=brokerOrderId,
                orderComplexity=orderComplexity
            )
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_place_gtt_order(tradingSymbol: str, exchange: str, transactionType: str, orderType: str,
                            product: str, validity: str, quantity: int, price: float, orderComplexity: str, 
                            instrumentId: str, gttType: str, gttValue: float)->dict:
    """Place GTT Order"""
    try:
        alice = get_alice_client()
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

@mcp.tool()
def get_gtt_order_book()-> dict:
    """Fetches GTT Order Book"""
    try:
        alice = get_alice_client()
        return{
            "status": "success",
            "data": alice.get_gtt_order_book()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_modify_gtt_order(brokerOrderId: str, instrumentId: str, tradingSymbol: str, 
                            exchange: str, orderType: str, product: str, validity: str, 
                            quantity: int, price: float, orderComplexity: str, 
                            gttType: str, gttValue: float)->dict:
    """Modify GTT Order"""
    try:
        alice = get_alice_client()
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

@mcp.tool()
def get_cancel_gtt_order(brokerOrderId: str)-> dict:
    """Cancel Order"""
    try:
        alice = get_alice_client()
        return{
            "status": "success",
            "data": alice.get_cancel_gtt_order(
                brokerOrderId=brokerOrderId
            )
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_limits()-> dict:
    """Get Limits"""
    try:
        alice = get_alice_client()
        return{
            "status": "success",
            "data": alice.get_limits()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    """Main function to run the MCP server"""
    mcp.run()

if __name__ == "__main__":
    main()