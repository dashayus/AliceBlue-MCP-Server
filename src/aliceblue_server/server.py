from pydantic import BaseModel, Field
from mcp.server.fastmcp import Context, FastMCP
from smithery.decorators import smithery
import requests
import hashlib
import time
from typing import Optional, Union
import json


BASE_URL = "https://ant.aliceblueonline.com"


class ConfigSchema(BaseModel):
    user_id: str = Field(description="Your AliceBlue User ID")
    auth_code: str = Field(description="Your AliceBlue Auth Code")
    api_secret: str = Field(description="Your AliceBlue API Secret")


@smithery.server(config_schema=ConfigSchema)
def create_server():
    server = FastMCP("AliceBlue Trading")

    class AliceBlue:
        def __init__(self, user_id: str, auth_code: str, api_secret: str):
            self.user_id = user_id
            self.auth_code = auth_code
            self.api_secret = api_secret
            self.user_session = None
            self.headers = None
            self.last_authentication = None
            self.timeout = 15  # API request timeout seconds

        def _make_request(self, method, url, **kwargs):
            max_retries = 2
            if 'timeout' not in kwargs:
                kwargs['timeout'] = self.timeout
            for attempt in range(max_retries):
                try:
                    if self.headers is None:
                        self.authenticate()
                    # Ensure headers updated for every request
                    kwargs['headers'] = self.headers
                    response = requests.request(method, url, **kwargs)
                    if response.status_code == 401:
                        if attempt < max_retries - 1:
                            self.authenticate()
                            continue
                        else:
                            raise Exception("Session expired and re-authentication failed")
                    return response
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    raise Exception(f"Connection error: {str(e)}")
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    raise e
            raise Exception("Max retries exceeded")

        def authenticate(self):
            try:
                raw_string = f"{self.user_id}{self.auth_code}{self.api_secret}"
                checksum = hashlib.sha256(raw_string.encode()).hexdigest()
                url = f"{BASE_URL}/open-api/od/v1/vendor/getUserDetails"
                payload = {"checkSum": checksum}
                response = requests.post(url, json=payload, timeout=10)
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
            except Exception as e:
                raise Exception(f"Authentication error: {str(e)}")

        def get_profile(self, ctx: Optional[Context] = None):
            if ctx:
                ctx.report_progress("Fetching user profile...")
            url = f"{BASE_URL}/open-api/od/v1/profile"
            response = self._make_request("GET", url, headers=self.headers)
            if response.status_code != 200:
                raise Exception(f"Profile Error {response.status_code}: {response.text}")
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")

        def get_holdings(self, ctx: Optional[Context] = None):
            if ctx:
                ctx.report_progress("Fetching holdings...")
            url = f"{BASE_URL}/open-api/od/v1/holdings/CNC"
            response = self._make_request("GET", url, headers=self.headers)
            if response.status_code != 200:
                raise Exception(f"Holding Error {response.status_code}: {response.text}")
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")

        def get_positions(self, ctx: Optional[Context] = None):
            if ctx:
                ctx.report_progress("Fetching positions...")
            url = f"{BASE_URL}/open-api/od/v1/positions"
            response = self._make_request("GET", url, headers=self.headers)
            if response.status_code != 200:
                raise Exception(f"Position Error {response.status_code}: {response.text}")
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")

        # Place order example (simplified)
        def get_place_order(
            self,
            instrument_id: str,
            exchange: str,
            transaction_type: str,
            quantity: int,
            order_type: str,
            product: str,
            order_complexity: str,
            price: float,
            validity: str,
            ctx: Optional[Context] = None
        ):
            if ctx:
                ctx.report_progress("Placing order...")
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
                "disclosedQuantity": 0,
                "source": "API"
            }]
            response = self._make_request("POST", url, headers=self.headers, json=payload)
            if response.status_code != 200:
                raise Exception(f"Order Place Error {response.status_code}: {response.text}")
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception(f"Non-JSON response: {response.text}")

        def test_connection(self, ctx: Optional[Context] = None):
            try:
                if self.authenticate():
                    if ctx:
                        ctx.report_progress("Authentication successful. Testing profile fetch...")
                    profile_data = self.get_profile(ctx)
                    return {
                        "status": "success",
                        "message": "Successfully connected to AliceBlue API",
                        "session_active": True,
                        "user_id": self.user_id,
                        "session_id": self.user_session,
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Authentication failed",
                        "session_active": False,
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Connection test failed: {str(e)}",
                    "session_active": False,
                }

    def get_alice_client(ctx: Context):
        if hasattr(ctx.session_state, "alice_client"):
            try:
                client = ctx.session_state.alice_client
                if client.headers is not None:
                    client.get_profile(ctx)
                return client
            except:
                pass
        config = ctx.session_config
        alice = AliceBlue(
            user_id=config.user_id,
            auth_code=config.auth_code,
            api_secret=config.api_secret
        )
        ctx.session_state.alice_client = alice
        return alice

    @server.tool()
    def test_connection(ctx: Context) -> dict:
        alice = get_alice_client(ctx)
        return alice.test_connection(ctx)

    @server.tool()
    def get_profile(ctx: Context) -> dict:
        try:
            alice = get_alice_client(ctx)
            data = alice.get_profile(ctx)
            return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_holdings(ctx: Context) -> dict:
        try:
            alice = get_alice_client(ctx)
            data = alice.get_holdings(ctx)
            return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def get_positions(ctx: Context) -> dict:
        try:
            alice = get_alice_client(ctx)
            data = alice.get_positions(ctx)
            return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @server.tool()
    def place_order(
        ctx: Context,
        instrument_id: str,
        exchange: str,
        transaction_type: str,
        quantity: int,
        order_type: str,
        product: str,
        order_complexity: str,
        price: float,
        validity: str
    ) -> dict:
        try:
            alice = get_alice_client(ctx)
            data = alice.get_place_order(
                instrument_id,
                exchange,
                transaction_type,
                quantity,
                order_type,
                product,
                order_complexity,
                price,
                validity,
                ctx
            )
            return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    return server
