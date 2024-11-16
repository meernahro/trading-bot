import traceback
from datetime import datetime
from typing import Dict, List, Optional

from binance.client import Client
from binance.exceptions import BinanceAPIException

from ..schemas import ExchangeType, MarketType
from ..utils.customLogger import get_logger
from ..utils.exceptions import ExchangeAPIError
from .base import ExchangeClientBase

logger = get_logger(__name__)


class BinanceSpotClient(ExchangeClientBase):
    """Binance Spot Exchange Client"""

    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        super().__init__(api_key, api_secret, testnet)
        try:
            self.client = Client(api_key, api_secret, testnet=testnet)
            # Test connection
            self.client.get_account()
        except BinanceAPIException as e:
            self.handle_error(e)
        except Exception as e:
            logger.error(f"Failed to initialize Binance client: {str(e)}")
            raise ExchangeAPIError(f"Binance initialization failed: {str(e)}")

    def get_account(self) -> Dict:
        """Get account information"""
        try:
            return self.client.get_account()
        except BinanceAPIException as e:
            self.handle_error(e)
        except Exception as e:
            logger.error(f"Error getting account information: {str(e)}")
            raise ExchangeAPIError(f"Failed to get account information: {str(e)}")

    def get_balance(self, asset: Optional[str] = None) -> Dict:
        """Get account balance for specific asset or all assets"""
        try:
            account = self.client.get_account()
            balances = {
                b["asset"]: {
                    "free": float(b["free"]),
                    "locked": float(b["locked"]),
                    "total": float(b["free"]) + float(b["locked"]),
                }
                for b in account["balances"]
                if float(b["free"]) > 0 or float(b["locked"]) > 0
            }
            return balances.get(asset, balances) if asset else balances
        except BinanceAPIException as e:
            self.handle_error(e)
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            raise ExchangeAPIError(f"Failed to get balance: {str(e)}")

    def get_symbol_price(self, symbol: str) -> Dict:
        """Get current price for a symbol"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return {
                "symbol": ticker["symbol"],
                "price": float(ticker["price"]),
                "timestamp": ticker["timestamp"] if "timestamp" in ticker else None,
            }
        except BinanceAPIException as e:
            self.handle_error(e)
        except Exception as e:
            logger.error(f"Error getting symbol price: {str(e)}")
            raise ExchangeAPIError(f"Failed to get symbol price: {str(e)}")

    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Optional[float] = None,
        price: Optional[float] = None,
        quote_order_qty: Optional[float] = None,
        time_in_force: Optional[str] = None,
    ) -> Dict:
        """Create a new order"""
        try:
            params = {
                "symbol": symbol,
                "side": side.upper(),
                "type": order_type.upper(),
            }

            # For market orders
            if order_type.upper() == "MARKET":
                if quote_order_qty and side.upper() == "BUY":
                    params["quoteOrderQty"] = quote_order_qty
                elif quantity:
                    params["quantity"] = quantity
                else:
                    raise ValueError(
                        "Either quantity or quote_order_qty must be provided"
                    )

            # For limit orders
            elif order_type.upper() == "LIMIT":
                if not all([quantity, price]):
                    raise ValueError(
                        "Both quantity and price are required for limit orders"
                    )
                params["quantity"] = quantity
                params["price"] = price
                params["timeInForce"] = time_in_force or "GTC"

            logger.info(f"Sending order to Binance with params: {params}")
            order = self.client.create_order(**params)
            logger.info(f"Received response from Binance: {order}")

            return self._format_order(order)

        except BinanceAPIException as e:
            self.handle_error(e)
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            logger.error(f"Full error: {traceback.format_exc()}")
            raise ExchangeAPIError(f"Failed to create order: {str(e)}")

    def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """Cancel an existing order"""
        try:
            order = self.client.cancel_order(symbol=symbol, orderId=order_id)
            return self._format_order(order)
        except BinanceAPIException as e:
            self.handle_error(e)
        except Exception as e:
            logger.error(f"Error canceling order: {str(e)}")
            raise ExchangeAPIError(f"Failed to cancel order: {str(e)}")

    def get_order(self, symbol: str, order_id: str) -> Dict:
        """Get order details"""
        try:
            order = self.client.get_order(symbol=symbol, orderId=order_id)
            return self._format_order(order)
        except BinanceAPIException as e:
            self.handle_error(e)
        except Exception as e:
            logger.error(f"Error getting order: {str(e)}")
            raise ExchangeAPIError(f"Failed to get order: {str(e)}")

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all open orders"""
        try:
            orders = self.client.get_open_orders(symbol=symbol)
            return [self._format_order(order) for order in orders]
        except BinanceAPIException as e:
            self.handle_error(e)
        except Exception as e:
            logger.error(f"Error getting open orders: {str(e)}")
            raise ExchangeAPIError(f"Failed to get open orders: {str(e)}")

    def get_order_history(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get order history"""
        try:
            orders = self.client.get_all_orders(symbol=symbol) if symbol else []
            return [self._format_order(order) for order in orders]
        except BinanceAPIException as e:
            self.handle_error(e)
        except Exception as e:
            logger.error(f"Error getting order history: {str(e)}")
            raise ExchangeAPIError(f"Failed to get order history: {str(e)}")

    def _format_order(self, order: Dict) -> Dict:
        """Format order response to standardized format"""
        # Calculate executed price from fills if available
        executed_price = None
        if order.get("fills"):
            total_cost = sum(
                float(fill["price"]) * float(fill["qty"]) for fill in order["fills"]
            )
            total_qty = sum(float(fill["qty"]) for fill in order["fills"])
            executed_price = total_cost / total_qty if total_qty > 0 else None

        # Get commission from fills
        commission = 0
        commission_asset = None
        if order.get("fills"):
            commission = sum(
                float(fill.get("commission", 0)) for fill in order["fills"]
            )
            commission_asset = (
                order["fills"][0].get("commissionAsset") if order["fills"] else None
            )

        return {
            "exchange": ExchangeType.BINANCE,  # Add exchange type
            "market_type": MarketType.SPOT,  # Add market type
            "order_id": str(order["orderId"]),
            "symbol": order["symbol"],
            "status": order["status"],
            "side": order["side"].lower(),  # Convert to lowercase to match enum
            "type": order["type"],
            "quantity": float(order["origQty"]),
            "executed_qty": float(order["executedQty"]),
            "price": float(order["price"]) if order["price"] != "0" else None,
            "executed_price": executed_price,  # Add executed price
            "created_at": datetime.fromtimestamp(order["transactTime"] / 1000)
            if order.get("transactTime")
            else None,
            "updated_at": datetime.fromtimestamp(order["workingTime"] / 1000)
            if order.get("workingTime")
            else None,
            "commission": commission,
            "commission_asset": commission_asset,
            "average_price": float(order.get("avgPrice", 0)) or None,
        }
