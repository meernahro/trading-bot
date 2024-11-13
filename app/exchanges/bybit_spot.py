from typing import Dict, Optional, List
from pybit.unified_trading import HTTP
from .base import ExchangeClientBase
from ..utils.exceptions import ExchangeAPIError
from ..utils.customLogger import get_logger
from datetime import datetime

logger = get_logger(__name__)

class BybitSpotClient(ExchangeClientBase):
    """Bybit Spot Exchange Client"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        super().__init__(api_key, api_secret, testnet)
        try:
            self.client = HTTP(
                testnet=testnet,
                api_key=api_key,
                api_secret=api_secret
            )
            
            # Test connection
            self.client.get_wallet_balance(accountType="SPOT")
        except Exception as e:
            logger.error(f"Failed to initialize Bybit client: {str(e)}")
            raise ExchangeAPIError(f"Bybit initialization failed: {str(e)}")

    def get_account(self) -> Dict:
        """Get account information"""
        try:
            wallet = self.client.get_wallet_balance(accountType="SPOT")
            account_info = self.client.get_api_key_information()
            
            return {
                'wallet': wallet['result'],
                'permissions': account_info['result']['permissions'],
                'account_type': 'spot'
            }
        except Exception as e:
            logger.error(f"Error getting account information: {str(e)}")
            raise ExchangeAPIError(f"Failed to get account information: {str(e)}")

    def get_balance(self, asset: Optional[str] = None) -> Dict:
        """Get account balance for specific asset or all assets"""
        try:
            response = self.client.get_wallet_balance(accountType="SPOT")
            balances = {}
            
            for coin in response['result']['list']:
                currency = coin['coin']
                if not asset or currency == asset:
                    balances[currency] = {
                        'free': float(coin['free']),
                        'locked': float(coin['locked']),
                        'total': float(coin['total'])
                    }
                    
            return balances.get(asset, balances) if asset else balances
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            raise ExchangeAPIError(f"Failed to get balance: {str(e)}")

    def get_symbol_price(self, symbol: str) -> Dict:
        """Get current price for a symbol"""
        try:
            ticker = self.client.get_tickers(
                category="spot",
                symbol=symbol
            )
            return {
                'symbol': symbol,
                'price': float(ticker['result']['list'][0]['lastPrice']),
                'timestamp': int(datetime.now().timestamp() * 1000)
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
                'category': 'spot',
                'symbol': symbol,
                'side': side.upper(),
                'orderType': order_type.upper(),
                'qty': str(quantity)
            }
            
            if order_type.upper() == 'LIMIT':
                if not price:
                    raise ValueError("Price is required for LIMIT orders")
                params['price'] = str(price)
            
            response = self.client.place_order(**params)
            
            if response['retCode'] == 0:
                order_id = response['result']['orderId']
                order_details = self.client.get_order_history(
                    category="spot",
                    orderId=order_id
                )
                return self._format_order(order_details['result']['list'][0])
            else:
                raise ExchangeAPIError(f"Order failed: {response['retMsg']}")
                
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            raise ExchangeAPIError(f"Failed to create order: {str(e)}")

    def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """Cancel an existing order"""
        try:
            response = self.client.cancel_order(
                category="spot",
                symbol=symbol,
                orderId=order_id
            )
            
            if response['retCode'] == 0:
                order_details = self.client.get_order_history(
                    category="spot",
                    orderId=order_id
                )
                return self._format_order(order_details['result']['list'][0])
            else:
                raise ExchangeAPIError(f"Cancel failed: {response['retMsg']}")
        except Exception as e:
            logger.error(f"Error canceling order: {str(e)}")
            raise ExchangeAPIError(f"Failed to cancel order: {str(e)}")

    def get_order(self, symbol: str, order_id: str) -> Dict:
        """Get order details"""
        try:
            response = self.client.get_order_history(
                category="spot",
                orderId=order_id
            )
            return self._format_order(response['result']['list'][0])
        except Exception as e:
            logger.error(f"Error getting order: {str(e)}")
            raise ExchangeAPIError(f"Failed to get order: {str(e)}")

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all open orders"""
        try:
            params = {'category': 'spot'}
            if symbol:
                params['symbol'] = symbol
                
            response = self.client.get_open_orders(**params)
            return [self._format_order(order) for order in response['result']['list']]
        except Exception as e:
            logger.error(f"Error getting open orders: {str(e)}")
            raise ExchangeAPIError(f"Failed to get open orders: {str(e)}")

    def get_order_book(self, symbol: str, limit: int = 100) -> Dict:
        """Get order book for a symbol"""
        try:
            response = self.client.get_orderbook(
                category="spot",
                symbol=symbol,
                limit=limit
            )
            return {
                'symbol': symbol,
                'bids': [[float(price), float(qty)] for price, qty in response['result']['b']],
                'asks': [[float(price), float(qty)] for price, qty in response['result']['a']],
                'timestamp': response['time']
            }
        except Exception as e:
            logger.error(f"Error getting order book: {str(e)}")
            raise ExchangeAPIError(f"Failed to get order book: {str(e)}")

    def _format_order(self, order: Dict) -> Dict:
        """Format order response to standardized format"""
        return {
            'order_id': order['orderId'],
            'symbol': order['symbol'],
            'status': self._map_order_status(order['orderStatus']),
            'side': order['side'].upper(),
            'type': order['orderType'].upper(),
            'quantity': float(order['qty']),
            'executed_qty': float(order['cumExecQty']),
            'price': float(order['price']) if order['price'] != '0' else None,
            'created_at': order['createdTime'],
            'updated_at': order['updatedTime'],
            'commission': float(order.get('cumExecFee', 0)),
            'commission_asset': order.get('feeTokenId'),
            'average_price': float(order['avgPrice']) if order['avgPrice'] != '0' else None
        }

    def _map_order_status(self, bybit_status: str) -> str:
        """Map Bybit specific order status to standard status"""
        status_map = {
            'Created': 'NEW',
            'New': 'NEW',
            'PartiallyFilled': 'PARTIALLY_FILLED',
            'Filled': 'FILLED',
            'Cancelled': 'CANCELED',
            'Rejected': 'REJECTED',
            'PendingCancel': 'PENDING_CANCEL'
        }
        return status_map.get(bybit_status, bybit_status.upper()) 