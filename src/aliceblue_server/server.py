# server.py
from pydantic import BaseModel, Field
from mcp.server.fastmcp import Context, FastMCP
from smithery.decorators import smithery
from typing import Optional, List, Dict, Any
import asyncio

# Import the official Ant-A3 SDK
try:
    from TradeMaster.TradeSync import TradeHub, TransactionType, OrderComplexity, ProductType, OrderType, PositionType, Exchange
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    # Mock classes for when SDK is not available
    class TradeHub:
        def __init__(self, user_id, auth_code, secret_key):
            self.user_id = user_id
            self.auth_code = auth_code
            self.secret_key = secret_key
            
    class TransactionType:
        Buy = "BUY"
        Sell = "SELL"
        
    class OrderComplexity:
        Regular = "Regular"
        AMO = "AMO"
        Cover = "CO"
        Bracket = "BO"
        
    class ProductType:
        Normal = "NORMAL"
        Intraday = "INTRADAY"
        Longterm = "LONGTERM"
        MTF = "MTF"
        GTT = "GTT"
        CNC = "CNC"
        BNPL = "BNPL"
        
    class OrderType:
        Limit = "LIMIT"
        Market = "MARKET"
        StopLoss = "SL"
        StopLossMarket = "SLM"
        
    class PositionType:
        posDAY = "DAY"
        posNET = "NET"
        posIOC = "IOC"
        
    class Exchange:
        NSE = "NSE"
        BSE = "BSE"
        NFO = "NFO"
        BFO = "BFO"
        CDS = "CDS"
        BCD = "BCD"
        NCO = "NCO"
        BCO = "BCO"
        MCX = "MCX"
        INDICES = "INDICES"
        NCDEX = "NCDEX"

# Configuration schema for session
class ConfigSchema(BaseModel):
    user_id: str = Field(description="Your AliceBlue User ID")
    auth_code: str = Field(description="Your AliceBlue Auth Code") 
    secret_key: str = Field(description="Your AliceBlue Secret Key")

@smithery.server(config_schema=ConfigSchema)
def create_server():
    """Create and configure the AliceBlue MCP server using official Ant-A3 SDK."""
    
    server = FastMCP("AliceBlue Trading Server")

    class AliceBlueClient:
        def __init__(self, user_id: str, auth_code: str, secret_key: str):
            self.user_id = user_id
            self.auth_code = auth_code
            self.secret_key = secret_key
            self.trade = None
            self.is_connected = False
            
        def connect(self):
            """Initialize the TradeHub connection"""
            try:
                if not SDK_AVAILABLE:
                    raise Exception("Ant-A3 SDK not available. Please install: pip install Ant-A3-tradehub-sdk-testing")
                
                self.trade = TradeHub(
                    user_id=self.user_id,
                    auth_code=self.auth_code,
                    secret_key=self.secret_key
                )
                
                # Get session ID to test connection
                session_result = self.trade.get_session_id()
                if session_result:
                    self.is_connected = True
                    return True
                else:
                    raise Exception("Failed to get session ID")
                    
            except Exception as e:
                raise Exception(f"Connection failed: {str(e)}")
        
        def get_session(self):
            """Get session ID"""
            if not self.is_connected:
                self.connect()
            return self.trade.get_session_id()
        
        def get_contract_master(self, exchange: str):
            """Download contract master for exchange"""
            if not self.is_connected:
                self.connect()
            return self.trade.get_contract_master(exchange=exchange)
        
        def get_instrument(self, exchange: str, symbol: str = None, token: str = None):
            """Get instrument by symbol or token"""
            if not self.is_connected:
                self.connect()
            return self.trade.get_instrument(exchange=exchange, symbol=symbol, token=token)
        
        def get_instrument_for_fno(self, exchange: str, symbol: str, expiry_date: str, strike: str, is_fut: bool, is_CE: bool):
            """Get F&O instrument"""
            if not self.is_connected:
                self.connect()
            return self.trade.get_instrument_for_fno(
                exchange=exchange,
                symbol=symbol,
                expiry_date=expiry_date,
                strike=strike,
                is_fut=is_fut,
                is_CE=is_CE
            )
        
        def get_profile(self):
            """Get user profile"""
            if not self.is_connected:
                self.connect()
            return self.trade.get_profile()
        
        def get_funds(self):
            """Get user funds"""
            if not self.is_connected:
                self.connect()
            return self.trade.get_funds()
        
        def get_positions(self):
            """Get user positions"""
            if not self.is_connected:
                self.connect()
            return self.trade.get_positions()
        
        def get_holdings(self, product: str):
            """Get user holdings"""
            if not self.is_connected:
                self.connect()
            return self.trade.get_holdings(product=product)
        
        def get_orderbook(self):
            """Get order book"""
            if not self.is_connected:
                self.connect()
            return self.trade.get_orderbook()
        
        def get_tradebook(self):
            """Get trade book"""
            if not self.is_connected:
                self.connect()
            return self.trade.get_tradebook()
        
        def get_order_history(self, brokerOrderId: str):
            """Get order history"""
            if not self.is_connected:
                self.connect()
            return self.trade.get_orderHistory(brokerOrderId=brokerOrderId)
        
        def place_order(self, **kwargs):
            """Place order with flexible parameters"""
            if not self.is_connected:
                self.connect()
            return self.trade.placeOrder(**kwargs)
        
        def modify_order(self, brokerOrderId: str, **kwargs):
            """Modify order"""
            if not self.is_connected:
                self.connect()
            return self.trade.modifyOrder(brokerOrderId=brokerOrderId, **kwargs)
        
        def cancel_order(self, brokerOrderId: str):
            """Cancel order"""
            if not self.is_connected:
                self.connect()
            return self.trade.cancelOrder(brokerOrderId=brokerOrderId)
        
        def exit_bracket_order(self, brokerOrderId: str, orderComplexity: str):
            """Exit bracket order"""
            if not self.is_connected:
                self.connect()
            return self.trade.exitBracketOrder(
                brokerOrderId=brokerOrderId,
                orderComplexity=orderComplexity
            )
        
        def position_square_off(self, **kwargs):
            """Position square off"""
            if not self.is_connected:
                self.connect()
            return self.trade.positionSqrOff(**kwargs)
        
        def single_order_margin(self, **kwargs):
            """Single order margin"""
            if not self.is_connected:
                self.connect()
            return self.trade.singleOrderMargin(**kwargs)
        
        def gtt_place_order(self, **kwargs):
            """GTT place order"""
            if not self.is_connected:
                self.connect()
            return self.trade.GTT_placeOrder(**kwargs)
        
        def gtt_modify_order(self, brokerOrderId: str, **kwargs):
            """GTT modify order"""
            if not self.is_connected:
                self.connect()
            return self.trade.GTT_modifyOrder(brokerOrderId=brokerOrderId, **kwargs)
        
        def gtt_cancel_order(self, brokerOrderId: str):
            """GTT cancel order"""
            if not self.is_connected:
                self.connect()
            return self.trade.GTT_cancelOrder(brokerOrderId=brokerOrderId)
        
        def test_connection(self):
            """Test connection to AliceBlue API"""
            try:
                if not SDK_AVAILABLE:
                    return {
                        "status": "error",
                        "message": "Ant-A3 SDK not available. Please install: pip install Ant-A3-tradehub-sdk-testing",
                        "sdk_available": False
                    }
                
                self.connect()
                session_id = self.get_session()
                
                return {
                    "status": "success",
                    "message": "Successfully connected to AliceBlue API",
                    "session_id": session_id,
                    "user_id": self.user_id,
                    "sdk_available": True,
                    "connected": self.is_connected
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Connection failed: {str(e)}",
                    "sdk_available": SDK_AVAILABLE,
                    "connected": False
                }

    def get_alice_client(ctx: Context):
        """Get or create AliceBlue client using session config"""
        if hasattr(ctx.session_state, 'alice_client'):
            return ctx.session_state.alice_client

        config = ctx.session_config
        
        client = AliceBlueClient(
            user_id=config.user_id,
            auth_code=config.auth_code, 
            secret_key=config.secret_key
        )
        
        ctx.session_state.alice_client = client
        return client

    # Tools
    @server.tool()
    def test_connection(ctx: Context) -> dict:
        """Test connection to AliceBlue API using official SDK"""
        try:
            client = get_alice_client(ctx)
            return client.test_connection()
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection test failed: {str(e)}",
                "sdk_available": SDK_AVAILABLE
            }

    @server.tool()
    def get_session(ctx: Context) -> dict:
        """Get session ID"""
        try:
            client = get_alice_client(ctx)
            session_id = client.get_session()
            return {
                "status": "success",
                "session_id": session_id,
                "user_id": client.user_id
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_contract_master(ctx: Context, exchange: str) -> dict:
        """Download contract master for specific exchange"""
        try:
            client = get_alice_client(ctx)
            result = client.get_contract_master(exchange=exchange)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_instrument(ctx: Context, exchange: str, symbol: Optional[str] = None, token: Optional[str] = None) -> dict:
        """Get instrument by symbol or token"""
        try:
            client = get_alice_client(ctx)
            result = client.get_instrument(exchange=exchange, symbol=symbol, token=token)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_instrument_for_fno(ctx: Context, exchange: str, symbol: str, expiry_date: str, strike: str, is_fut: bool, is_CE: bool) -> dict:
        """Get F&O instrument"""
        try:
            client = get_alice_client(ctx)
            result = client.get_instrument_for_fno(
                exchange=exchange,
                symbol=symbol,
                expiry_date=expiry_date,
                strike=strike,
                is_fut=is_fut,
                is_CE=is_CE
            )
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_profile(ctx: Context) -> dict:
        """Get user profile details"""
        try:
            client = get_alice_client(ctx)
            result = client.get_profile()
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_funds(ctx: Context) -> dict:
        """Get user funds"""
        try:
            client = get_alice_client(ctx)
            result = client.get_funds()
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_positions(ctx: Context) -> dict:
        """Get user positions"""
        try:
            client = get_alice_client(ctx)
            result = client.get_positions()
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_holdings(ctx: Context, product: str) -> dict:
        """Get user holdings for specific product type"""
        try:
            client = get_alice_client(ctx)
            result = client.get_holdings(product=product)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_orderbook(ctx: Context) -> dict:
        """Get order book"""
        try:
            client = get_alice_client(ctx)
            result = client.get_orderbook()
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_tradebook(ctx: Context) -> dict:
        """Get trade book"""
        try:
            client = get_alice_client(ctx)
            result = client.get_tradebook()
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_order_history(ctx: Context, brokerOrderId: str) -> dict:
        """Get order history"""
        try:
            client = get_alice_client(ctx)
            result = client.get_order_history(brokerOrderId=brokerOrderId)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Order Management Tools
    @server.tool()
    def place_order(
        ctx: Context,
        instrumentId: Optional[str] = None,
        exchange: Optional[str] = None,
        instrument: Optional[dict] = None,
        transactionType: str = "BUY",
        quantity: str = "1",
        orderComplexity: str = "Regular",
        product: str = "CNC",
        orderType: str = "MARKET",
        price: str = "",
        slTriggerPrice: str = "",
        slLegPrice: str = "",
        targetLegPrice: str = "",
        validity: str = "DAY",
        trailingSlAmount: str = "",
        disclosedQuantity: str = "",
        marketProtectionPercent: str = "",
        apiOrderSource: str = "",
        algoId: str = "",
        orderTag: str = ""
    ) -> dict:
        """Place a new order"""
        try:
            client = get_alice_client(ctx)
            
            params = {
                "transactionType": transactionType,
                "quantity": quantity,
                "orderComplexity": orderComplexity,
                "product": product,
                "orderType": orderType,
                "price": price,
                "slTriggerPrice": slTriggerPrice,
                "slLegPrice": slLegPrice,
                "targetLegPrice": targetLegPrice,
                "validity": validity,
                "trailingSlAmount": trailingSlAmount,
                "disclosedQuantity": disclosedQuantity,
                "marketProtectionPercent": marketProtectionPercent,
                "apiOrderSource": apiOrderSource,
                "algoId": algoId,
                "orderTag": orderTag
            }
            
            if instrumentId and exchange:
                params["instrumentId"] = instrumentId
                params["exchange"] = exchange
            elif instrument:
                params["instrument"] = instrument
            else:
                return {"status": "error", "message": "Either provide instrumentId+exchange or instrument"}
            
            result = client.place_order(**params)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def modify_order(
        ctx: Context,
        brokerOrderId: str,
        price: str = "",
        slTriggerPrice: str = "",
        slLegPrice: str = "",
        targetLegPrice: str = "",
        quantity: str = "",
        orderType: str = "LIMIT",
        trailingSLAmount: str = "",
        validity: str = "DAY",
        disclosedQuantity: str = "",
        marketProtectionPrecent: str = "",
        deviceId: str = ""
    ) -> dict:
        """Modify an existing order"""
        try:
            client = get_alice_client(ctx)
            
            params = {
                "brokerOrderId": brokerOrderId,
                "price": price,
                "slTriggerPrice": slTriggerPrice,
                "slLegPrice": slLegPrice,
                "targetLegPrice": targetLegPrice,
                "quantity": quantity,
                "orderType": orderType,
                "trailingSLAmount": trailingSLAmount,
                "validity": validity,
                "disclosedQuantity": disclosedQuantity,
                "marketProtectionPrecent": marketProtectionPrecent,
                "deviceId": deviceId
            }
            
            result = client.modify_order(**params)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def cancel_order(ctx: Context, brokerOrderId: str) -> dict:
        """Cancel an order"""
        try:
            client = get_alice_client(ctx)
            result = client.cancel_order(brokerOrderId=brokerOrderId)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def exit_bracket_order(ctx: Context, brokerOrderId: str, orderComplexity: str) -> dict:
        """Exit bracket order"""
        try:
            client = get_alice_client(ctx)
            result = client.exit_bracket_order(
                brokerOrderId=brokerOrderId,
                orderComplexity=orderComplexity
            )
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def position_square_off(
        ctx: Context,
        instrumentId: Optional[str] = None,
        exchange: Optional[str] = None,
        instrument: Optional[dict] = None,
        transactionType: str = "BUY",
        quantity: str = "1",
        orderComplexity: str = "Regular",
        product: str = "CNC",
        orderType: str = "MARKET",
        price: str = "",
        slTriggerPrice: str = "",
        slLegPrice: str = "",
        targetLegPrice: str = "",
        validity: str = "DAY",
        trailingSlAmount: str = "",
        disclosedQuantity: str = "",
        marketProtectionPercent: str = "",
        apiOrderSource: str = "",
        algoId: str = "",
        orderTag: str = ""
    ) -> dict:
        """Square off a position"""
        try:
            client = get_alice_client(ctx)
            
            params = {
                "transactionType": transactionType,
                "quantity": quantity,
                "orderComplexity": orderComplexity,
                "product": product,
                "orderType": orderType,
                "price": price,
                "slTriggerPrice": slTriggerPrice,
                "slLegPrice": slLegPrice,
                "targetLegPrice": targetLegPrice,
                "validity": validity,
                "trailingSlAmount": trailingSlAmount,
                "disclosedQuantity": disclosedQuantity,
                "marketProtectionPercent": marketProtectionPercent,
                "apiOrderSource": apiOrderSource,
                "algoId": algoId,
                "orderTag": orderTag
            }
            
            if instrumentId and exchange:
                params["instrumentId"] = instrumentId
                params["exchange"] = exchange
            elif instrument:
                params["instrument"] = instrument
            else:
                return {"status": "error", "message": "Either provide instrumentId+exchange or instrument"}
            
            result = client.position_square_off(**params)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def single_order_margin(
        ctx: Context,
        instrumentId: Optional[str] = None,
        exchange: Optional[str] = None,
        instrument: Optional[dict] = None,
        transactionType: str = "BUY",
        quantity: str = "1",
        orderComplexity: str = "Regular",
        product: str = "INTRADAY",
        orderType: str = "MARKET",
        price: str = "",
        slTriggerPrice: str = "",
        slLegPrice: str = ""
    ) -> dict:
        """Check single order margin"""
        try:
            client = get_alice_client(ctx)
            
            params = {
                "transactionType": transactionType,
                "quantity": quantity,
                "orderComplexity": orderComplexity,
                "product": product,
                "orderType": orderType,
                "price": price,
                "slTriggerPrice": slTriggerPrice,
                "slLegPrice": slLegPrice
            }
            
            if instrumentId and exchange:
                params["instrumentId"] = instrumentId
                params["exchange"] = exchange
            elif instrument:
                params["instrument"] = instrument
            else:
                return {"status": "error", "message": "Either provide instrumentId+exchange or instrument"}
            
            result = client.single_order_margin(**params)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # GTT Order Tools
    @server.tool()
    def gtt_place_order(
        ctx: Context,
        instrument: dict,
        transactionType: str = "BUY",
        quantity: str = "1",
        orderComplexity: str = "Regular",
        product: str = "INTRADAY",
        orderType: str = "LIMIT",
        price: str = "",
        gttValue: str = "",
        validity: str = "DAY"
    ) -> dict:
        """Place GTT order"""
        try:
            client = get_alice_client(ctx)
            
            params = {
                "instrument": instrument,
                "transactionType": transactionType,
                "quantity": quantity,
                "orderComplexity": orderComplexity,
                "product": product,
                "orderType": orderType,
                "price": price,
                "gttValue": gttValue,
                "validity": validity
            }
            
            result = client.gtt_place_order(**params)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def gtt_modify_order(
        ctx: Context,
        brokerOrderId: str,
        instrument: dict,
        quantity: str = "1",
        orderComplexity: str = "Regular",
        product: str = "INTRADAY",
        orderType: str = "LIMIT",
        price: str = "",
        gttValue: str = "",
        validity: str = "DAY"
    ) -> dict:
        """Modify GTT order"""
        try:
            client = get_alice_client(ctx)
            
            params = {
                "brokerOrderId": brokerOrderId,
                "instrument": instrument,
                "quantity": quantity,
                "orderComplexity": orderComplexity,
                "product": product,
                "orderType": orderType,
                "price": price,
                "gttValue": gttValue,
                "validity": validity
            }
            
            result = client.gtt_modify_order(**params)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def gtt_cancel_order(ctx: Context, brokerOrderId: str) -> dict:
        """Cancel GTT order"""
        try:
            client = get_alice_client(ctx)
            result = client.gtt_cancel_order(brokerOrderId=brokerOrderId)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_available_exchanges(ctx: Context) -> dict:
        """Get list of available exchanges"""
        exchanges = {
            "NSE": "National Stock Exchange",
            "BSE": "Bombay Stock Exchange", 
            "NFO": "NSE Futures & Options",
            "BFO": "BSE Futures & Options",
            "CDS": "Currency Derivatives Segment (NSE)",
            "BCD": "BSE Currency Derivatives",
            "NCO": "NSE Commodities",
            "BCO": "BSE Commodities",
            "MCX": "Multi Commodity Exchange",
            "INDICES": "Index data (NSE/BSE indices)",
            "NCDEX": "National Commodity & Derivatives Exchange"
        }
        return {"status": "success", "data": exchanges}

    @server.tool()
    def get_available_order_types(ctx: Context) -> dict:
        """Get list of available order types"""
        order_types = {
            "LIMIT": "Limit Order",
            "MARKET": "Market Order", 
            "SL": "Stop Loss Limit Order",
            "SLM": "Stop Loss Market Order"
        }
        return {"status": "success", "data": order_types}

    @server.tool()
    def get_available_products(ctx: Context) -> dict:
        """Get list of available product types"""
        products = {
            "NORMAL": "Normal order",
            "INTRADAY": "Margin Intraday Square-off",
            "LONGTERM": "Delivery-based, long-term holding", 
            "MTF": "Margin Trading Facility",
            "GTT": "Good Till Triggered",
            "CNC": "Cash and Carry",
            "BNPL": "Buy Now Pay Later"
        }
        return {"status": "success", "data": products}

    return server