from typing import Dict, Optional, List
from okx.PublicData import PublicAPI
from okx.Account import AccountAPI
from okx.Trade import TradeAPI
from okx.MarketData import MarketAPI
from .base import ExchangeClientBase
from ..utils.exceptions import ExchangeAPIError
from ..utils.customLogger import get_logger

logger = get_logger(__name__)

class OKXSpotClient(ExchangeClientBase):
    """OKX Spot Exchange Client"""
    
    def __init__(self, api_key: str, api_secret: str, passphrase: str, testnet: bool = False):
        super().__init__(api_key, api_secret, testnet)
        try:
            # OKX requires separate clients for different functionalities
            kwargs = {
                "api_key": api_key,
                "api_secret_key": api_secret,  # Changed to api_secret_key
                "passphrase": passphrase,
                "flag": "1" if testnet else "0",  # 0-Production 1-Sandbox
                "debug": False
            }
            
            self.account_client = AccountAPI(**kwargs)
            self.trade_client = TradeAPI(**kwargs)
            self.market_client = MarketAPI(**kwargs)
            self.public_client = PublicAPI(**kwargs)
            
            # Test connection
            self.account_client.get_account_balance()
        except Exception as e:
            logger.error(f"Failed to initialize OKX client: {str(e)}")
            raise ExchangeAPIError(f"OKX initialization failed: {str(e)}")

    def get_account(self) -> Dict:
        """Get account information"""
        try:
            balance = self.account_client.get_account_balance()
            position_risk = self.account_client.get_position_risk()
            
            return {
                'balance': balance['data'][0],
                'position_risk': position_risk['data'],
                'account_type': 'spot'
            }
        except Exception as e:
            logger.error(f"Error getting account information: {str(e)}")
            raise ExchangeAPIError(f"Failed to get account information: {str(e)}")

    def get_balance(self, asset: Optional[str] = None) -> Dict:
        """Get account balance for specific asset or all assets"""
        try:
            response = self.account_client.get_account_balance()
            if not response['code'] == '0':
                raise ExchangeAPIError(f"Failed to get balance: {response['msg']}")
                
            balances = {}
            for currency in response['data'][0]['details']:
                ccy = currency['ccy']
                if not asset or ccy == asset:
                    balances[ccy] = {
                        'free': float(currency['availBal']),
                        'locked': float(currency['frozenBal']),
                        'total': float(currency['cashBal'])
                    }
                    
            return balances.get(asset, balances) if asset else balances
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            raise ExchangeAPIError(f"Failed to get balance: {str(e)}")

    def get_symbol_price(self, symbol: str) -> Dict:
        """Get current price for a symbol"""
        try:
            ticker = self.market_client.get_ticker(instId=symbol)
            return {
                'symbol': symbol,
                'price': float(ticker['data'][0]['last']),
                'timestamp': ticker['data'][0]['ts']
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
                'instId': symbol,
                'tdMode': 'cash',  # cash for spot trading
                'side': side.lower(),
                'ordType': order_type.lower(),
                'sz': str(quantity)
            }
            
            if order_type.upper() == 'LIMIT':
                if not price:
                    raise ValueError("Price is required for LIMIT orders")
                params['px'] = str(price)
            
            response = self.trade_client.place_order(**params)
            
            if response['code'] == '0':
                order_id = response['data'][0]['ordId']
                order_details = self.trade_client.get_order(instId=symbol, ordId=order_id)
                if order_details['code'] == '0':
                    return self._format_order(order_details['data'][0])
                else:
                    raise ExchangeAPIError(f"Failed to get order details: {order_details['msg']}")
            else:
                raise ExchangeAPIError(f"Order failed: {response['msg']}")
                
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            raise ExchangeAPIError(f"Failed to create order: {str(e)}")

    def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """Cancel an existing order"""
        try:
            response = self.trade_client.cancel_order(instId=symbol, ordId=order_id)
            if response['code'] == '0':
                order_details = self.trade_client.get_order(instId=symbol, ordId=order_id)
                return self._format_order(order_details['data'][0])
            else:
                raise ExchangeAPIError(f"Cancel failed: {response['msg']}")
        except Exception as e:
            logger.error(f"Error canceling order: {str(e)}")
            raise ExchangeAPIError(f"Failed to cancel order: {str(e)}")

    def get_order(self, symbol: str, order_id: str) -> Dict:
        """Get order details"""
        try:
            response = self.trade_client.get_order(instId=symbol, ordId=order_id)
            return self._format_order(response['data'][0])
        except Exception as e:
            logger.error(f"Error getting order: {str(e)}")
            raise ExchangeAPIError(f"Failed to get order: {str(e)}")

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all open orders"""
        try:
            params = {'instType': 'SPOT'}
            if symbol:
                params['instId'] = symbol
                
            response = self.trade_client.get_order_list(**params)
            return [self._format_order(order) for order in response['data']]
        except Exception as e:
            logger.error(f"Error getting open orders: {str(e)}")
            raise ExchangeAPIError(f"Failed to get open orders: {str(e)}")

    def get_order_book(self, symbol: str, limit: int = 100) -> Dict:
        """Get order book for a symbol"""
        try:
            response = self.market_client.get_orderbook(instId=symbol, sz=str(limit))
            if response['code'] != '0':
                raise ExchangeAPIError(f"Failed to get order book: {response['msg']}")
                
            return {
                'symbol': symbol,
                'bids': [[float(price), float(qty)] for price, qty, *_ in response['data'][0]['bids']],
                'asks': [[float(price), float(qty)] for price, qty, *_ in response['data'][0]['asks']],
                'timestamp': int(response['data'][0]['ts'])
            }
        except Exception as e:
            logger.error(f"Error getting order book: {str(e)}")
            raise ExchangeAPIError(f"Failed to get order book: {str(e)}")

    def _format_order(self, order: Dict) -> Dict:
        """Format order response to standardized format"""
        return {
            'order_id': order['ordId'],
            'symbol': order['instId'],
            'status': self._map_order_status(order['state']),
            'side': order['side'].upper(),
            'type': order['ordType'].upper(),
            'quantity': float(order['sz']),
            'executed_qty': float(order['fillSz']),
            'price': float(order['px']) if order['px'] else None,
            'created_at': int(order['cTime']),
            'updated_at': int(order['uTime']),
            'commission': float(order.get('fee', 0)),
            'commission_asset': order.get('feeCcy'),
            'average_price': float(order['avgPx']) if order['avgPx'] else None
        }

    def _map_order_status(self, okx_status: str) -> str:
        """Map OKX specific order status to standard status"""
        status_map = {
            'live': 'NEW',
            'partially_filled': 'PARTIALLY_FILLED',
            'filled': 'FILLED',
            'canceled': 'CANCELED',
            'failed': 'REJECTED'
        }
        return status_map.get(okx_status, okx_status.upper()) 