from typing import Dict, Optional, List
from kucoin.client import Market, Trade, User
from .base import ExchangeClientBase
from ..utils.exceptions import ExchangeAPIError
from ..utils.customLogger import get_logger

logger = get_logger(__name__)

class KuCoinSpotClient(ExchangeClientBase):
    """KuCoin Spot Exchange Client"""
    
    def __init__(self, api_key: str, api_secret: str, passphrase: str, testnet: bool = False):
        super().__init__(api_key, api_secret, testnet)
        try:
            # KuCoin requires separate clients for different functionalities
            self.market_client = Market(
                key=api_key,
                secret=api_secret,
                passphrase=passphrase,
                is_sandbox=testnet
            )
            self.trade_client = Trade(
                key=api_key,
                secret=api_secret,
                passphrase=passphrase,
                is_sandbox=testnet
            )
            self.user_client = User(
                key=api_key,
                secret=api_secret,
                passphrase=passphrase,
                is_sandbox=testnet
            )
            
            # Test connection
            self.user_client.get_account_list()
        except Exception as e:
            logger.error(f"Failed to initialize KuCoin client: {str(e)}")
            raise ExchangeAPIError(f"KuCoin initialization failed: {str(e)}")

    def get_account(self) -> Dict:
        """Get account information"""
        try:
            accounts = self.user_client.get_account_list()
            return {
                'accounts': accounts,
                'account_type': 'spot',
                'permissions': ['spot', 'margin'] # KuCoin specific
            }
        except Exception as e:
            logger.error(f"Error getting account information: {str(e)}")
            raise ExchangeAPIError(f"Failed to get account information: {str(e)}")

    def get_balance(self, asset: Optional[str] = None) -> Dict:
        """Get account balance for specific asset or all assets"""
        try:
            if asset:
                accounts = self.user_client.get_account_list(currency=asset)
            else:
                accounts = self.user_client.get_account_list()
                
            balances = {}
            for account in accounts:
                currency = account['currency']
                if currency not in balances:
                    balances[currency] = {
                        'free': float(account['available']),
                        'locked': float(account['holds']),
                        'total': float(account['balance'])
                    }
                else:
                    # Aggregate balances from different account types
                    balances[currency]['free'] += float(account['available'])
                    balances[currency]['locked'] += float(account['holds'])
                    balances[currency]['total'] += float(account['balance'])
                    
            return balances.get(asset, balances) if asset else balances
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            raise ExchangeAPIError(f"Failed to get balance: {str(e)}")

    def get_symbol_price(self, symbol: str) -> Dict:
        """Get current price for a symbol"""
        try:
            ticker = self.market_client.get_ticker(symbol)
            return {
                'symbol': symbol,
                'price': float(ticker['price']),
                'timestamp': ticker['time']
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
                'side': side.lower(),  # KuCoin uses lowercase
                'type': order_type.lower(),  # KuCoin uses lowercase
                'size': quantity
            }
            
            if order_type.upper() == 'LIMIT':
                if not price:
                    raise ValueError("Price is required for LIMIT orders")
                params['price'] = price
                
            order = self.trade_client.create_order(**params)
            return self._format_order(order)
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            raise ExchangeAPIError(f"Failed to create order: {str(e)}")

    def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """Cancel an existing order"""
        try:
            result = self.trade_client.cancel_order(order_id)
            order = self.trade_client.get_order_details(order_id)
            return self._format_order(order)
        except Exception as e:
            logger.error(f"Error canceling order: {str(e)}")
            raise ExchangeAPIError(f"Failed to cancel order: {str(e)}")

    def get_order(self, symbol: str, order_id: str) -> Dict:
        """Get order details"""
        try:
            order = self.trade_client.get_order_details(order_id)
            return self._format_order(order)
        except Exception as e:
            logger.error(f"Error getting order: {str(e)}")
            raise ExchangeAPIError(f"Failed to get order: {str(e)}")

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all open orders"""
        try:
            params = {'status': 'active'}
            if symbol:
                params['symbol'] = symbol
            orders = self.trade_client.get_order_list(**params)
            return [self._format_order(order) for order in orders['items']]
        except Exception as e:
            logger.error(f"Error getting open orders: {str(e)}")
            raise ExchangeAPIError(f"Failed to get open orders: {str(e)}")

    def get_order_book(self, symbol: str, limit: int = 100) -> Dict:
        """Get order book for a symbol"""
        try:
            depth = self.market_client.get_aggregated_orderv3(symbol)
            return {
                'symbol': symbol,
                'bids': [[float(price), float(qty)] for price, qty in depth['bids']],
                'asks': [[float(price), float(qty)] for price, qty in depth['asks']],
                'timestamp': depth['time']
            }
        except Exception as e:
            logger.error(f"Error getting order book: {str(e)}")
            raise ExchangeAPIError(f"Failed to get order book: {str(e)}")

    def _format_order(self, order: Dict) -> Dict:
        """Format order response to standardized format"""
        return {
            'order_id': order['id'],
            'symbol': order['symbol'],
            'status': order['status'].upper(),  # Standardize status to uppercase
            'side': order['side'].upper(),
            'type': order['type'].upper(),
            'quantity': float(order['size']),
            'executed_qty': float(order.get('dealSize', 0)),
            'price': float(order['price']) if order.get('price') else None,
            'created_at': order['createdAt'],
            'updated_at': order.get('updatedAt'),
            'commission': float(order.get('fee', 0)),
            'commission_asset': order.get('feeCurrency'),
            'average_price': float(order.get('dealFunds', 0)) / float(order.get('dealSize', 1)) if float(order.get('dealSize', 0)) > 0 else None
        } 