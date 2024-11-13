from typing import Dict, Optional, List
from mexc_api import spot
from .base import ExchangeClientBase
from ..utils.exceptions import ExchangeAPIError
from ..utils.customLogger import get_logger

logger = get_logger(__name__)

class MEXCSpotClient(ExchangeClientBase):
    """MEXC Spot Exchange Client"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        super().__init__(api_key, api_secret, testnet)
        try:
            # MEXC uses different URLs for testnet
            base_url = "https://api-testnet.mexc.com" if testnet else "https://api.mexc.com"
            self.client = spot.SpotAPI(
                api_key=api_key,
                api_secret=api_secret,
                base_url=base_url
            )
            # Test connection
            self.client.account_info()
        except Exception as e:
            logger.error(f"Failed to initialize MEXC client: {str(e)}")
            raise ExchangeAPIError(f"MEXC initialization failed: {str(e)}")

    def get_account(self) -> Dict:
        """Get account information"""
        try:
            return self.client.account_info()
        except Exception as e:
            logger.error(f"Error getting account information: {str(e)}")
            raise ExchangeAPIError(f"Failed to get account information: {str(e)}")

    def get_balance(self, asset: Optional[str] = None) -> Dict:
        """Get account balance for specific asset or all assets"""
        try:
            account = self.client.account_info()
            balances = {
                b['asset']: {
                    'free': float(b['free']),
                    'locked': float(b['locked']),
                    'total': float(b['free']) + float(b['locked'])
                }
                for b in account['balances']
                if float(b['free']) > 0 or float(b['locked']) > 0
            }
            return balances.get(asset, balances) if asset else balances
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            raise ExchangeAPIError(f"Failed to get balance: {str(e)}")

    def get_symbol_price(self, symbol: str) -> Dict:
        """Get current price for a symbol"""
        try:
            ticker = self.client.ticker_price(symbol=symbol)
            return {
                'symbol': ticker['symbol'],
                'price': float(ticker['price']),
                'timestamp': ticker.get('timestamp')
            }
        except Exception as e:
            logger.error(f"Error getting symbol price: {str(e)}")
            raise ExchangeAPIError(f"Failed to get symbol price: {str(e)}")

    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None
    ) -> Dict:
        """Create a new order"""
        try:
            params = {
                'symbol': symbol,
                'side': side.upper(),
                'type': order_type.upper(),
                'quantity': quantity
            }
            
            if order_type.upper() == 'LIMIT':
                if not price:
                    raise ValueError("Price is required for LIMIT orders")
                params['price'] = price
                params['timeInForce'] = 'GTC'

            order = self.client.create_order(**params)
            return self._format_order(order)
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            raise ExchangeAPIError(f"Failed to create order: {str(e)}")

    def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """Cancel an existing order"""
        try:
            order = self.client.cancel_order(
                symbol=symbol,
                orderId=order_id
            )
            return self._format_order(order)
        except Exception as e:
            logger.error(f"Error canceling order: {str(e)}")
            raise ExchangeAPIError(f"Failed to cancel order: {str(e)}")

    def get_order(self, symbol: str, order_id: str) -> Dict:
        """Get order details"""
        try:
            order = self.client.get_order(
                symbol=symbol,
                orderId=order_id
            )
            return self._format_order(order)
        except Exception as e:
            logger.error(f"Error getting order: {str(e)}")
            raise ExchangeAPIError(f"Failed to get order: {str(e)}")

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all open orders"""
        try:
            orders = self.client.get_open_orders(symbol=symbol)
            return [self._format_order(order) for order in orders]
        except Exception as e:
            logger.error(f"Error getting open orders: {str(e)}")
            raise ExchangeAPIError(f"Failed to get open orders: {str(e)}")

    def get_order_history(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get order history"""
        try:
            orders = self.client.get_orders(symbol=symbol) if symbol else []
            return [self._format_order(order) for order in orders]
        except Exception as e:
            logger.error(f"Error getting order history: {str(e)}")
            raise ExchangeAPIError(f"Failed to get order history: {str(e)}")

    def get_order_book(self, symbol: str, limit: int = 100) -> Dict:
        """Get order book for a symbol"""
        try:
            depth = self.client.depth(symbol=symbol, limit=limit)
            return {
                'symbol': symbol,
                'bids': [[float(price), float(qty)] for price, qty in depth['bids']],
                'asks': [[float(price), float(qty)] for price, qty in depth['asks']],
                'timestamp': depth.get('timestamp', None)
            }
        except Exception as e:
            logger.error(f"Error getting order book: {str(e)}")
            raise ExchangeAPIError(f"Failed to get order book: {str(e)}")

    def _format_order(self, order: Dict) -> Dict:
        """Format order response to standardized format"""
        return {
            'order_id': str(order['orderId']),
            'symbol': order['symbol'],
            'status': order['status'],
            'side': order['side'],
            'type': order['type'],
            'quantity': float(order['origQty']),
            'executed_qty': float(order['executedQty']),
            'price': float(order['price']) if order['price'] != '0' else None,
            'created_at': order['time'],
            'updated_at': order.get('updateTime'),
            'commission': float(order.get('commission', 0)),
            'commission_asset': order.get('commissionAsset'),
            'average_price': float(order.get('avgPrice', 0)) or None
        } 