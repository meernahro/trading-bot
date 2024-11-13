from typing import Dict, Optional, List
from binance.client import Client
from binance.exceptions import BinanceAPIException
from .base import ExchangeClientBase
from ..utils.exceptions import ExchangeAPIError
from ..utils.customLogger import get_logger

logger = get_logger(__name__)

class BinanceSpotClient(ExchangeClientBase):
    """Binance Spot Exchange Client"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        super().__init__(api_key, api_secret, testnet)
        try:
            self.client = Client(
                api_key,
                api_secret,
                testnet=testnet
            )
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
                b['asset']: {
                    'free': float(b['free']),
                    'locked': float(b['locked']),
                    'total': float(b['free']) + float(b['locked'])
                }
                for b in account['balances']
                if float(b['free']) > 0 or float(b['locked']) > 0
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
                'symbol': ticker['symbol'],
                'price': float(ticker['price']),
                'timestamp': ticker['timestamp'] if 'timestamp' in ticker else None
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
        except BinanceAPIException as e:
            self.handle_error(e)
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
        except BinanceAPIException as e:
            self.handle_error(e)
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

    def get_order_book(self, symbol: str, limit: int = 100) -> Dict:
        """Get order book for a symbol"""
        try:
            depth = self.client.get_order_book(symbol=symbol, limit=limit)
            return {
                'symbol': symbol,
                'bids': [[float(price), float(qty)] for price, qty in depth['bids']],
                'asks': [[float(price), float(qty)] for price, qty in depth['asks']],
                'timestamp': depth['lastUpdateId']
            }
        except BinanceAPIException as e:
            self.handle_error(e)
        except Exception as e:
            logger.error(f"Error getting order book: {str(e)}")
            raise ExchangeAPIError(f"Failed to get order book: {str(e)}")

    def get_recent_trades(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Get recent trades for a symbol"""
        try:
            trades = self.client.get_recent_trades(symbol=symbol, limit=limit)
            return [{
                'id': trade['id'],
                'price': float(trade['price']),
                'quantity': float(trade['qty']),
                'timestamp': trade['time'],
                'maker': trade['isBuyerMaker'],
                'best_match': trade['isBestMatch']
            } for trade in trades]
        except BinanceAPIException as e:
            self.handle_error(e)
        except Exception as e:
            logger.error(f"Error getting recent trades: {str(e)}")
            raise ExchangeAPIError(f"Failed to get recent trades: {str(e)}")

    def get_klines(self, symbol: str, interval: str, limit: int = 500) -> List[Dict]:
        """Get klines/candlestick data"""
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            return [{
                'timestamp': k[0],
                'open': float(k[1]),
                'high': float(k[2]),
                'low': float(k[3]),
                'close': float(k[4]),
                'volume': float(k[5]),
                'close_time': k[6],
                'quote_volume': float(k[7]),
                'trades': k[8],
                'taker_buy_base': float(k[9]),
                'taker_buy_quote': float(k[10])
            } for k in klines]
        except BinanceAPIException as e:
            self.handle_error(e)
        except Exception as e:
            logger.error(f"Error getting klines: {str(e)}")
            raise ExchangeAPIError(f"Failed to get klines: {str(e)}")

    def get_24h_ticker(self, symbol: str) -> Dict:
        """Get 24-hour ticker statistics"""
        try:
            ticker = self.client.get_ticker(symbol=symbol)
            return {
                'symbol': ticker['symbol'],
                'price_change': float(ticker['priceChange']),
                'price_change_percent': float(ticker['priceChangePercent']),
                'weighted_avg_price': float(ticker['weightedAvgPrice']),
                'prev_close_price': float(ticker['prevClosePrice']),
                'last_price': float(ticker['lastPrice']),
                'last_qty': float(ticker['lastQty']),
                'bid_price': float(ticker['bidPrice']),
                'ask_price': float(ticker['askPrice']),
                'open_price': float(ticker['openPrice']),
                'high_price': float(ticker['highPrice']),
                'low_price': float(ticker['lowPrice']),
                'volume': float(ticker['volume']),
                'quote_volume': float(ticker['quoteVolume']),
                'open_time': ticker['openTime'],
                'close_time': ticker['closeTime'],
                'count': ticker['count']
            }
        except BinanceAPIException as e:
            self.handle_error(e)
        except Exception as e:
            logger.error(f"Error getting 24h ticker: {str(e)}")
            raise ExchangeAPIError(f"Failed to get 24h ticker: {str(e)}")

    def get_exchange_info(self) -> Dict:
        """Get exchange trading rules and symbol information"""
        try:
            info = self.client.get_exchange_info()
            return {
                'timezone': info['timezone'],
                'server_time': info['serverTime'],
                'rate_limits': info['rateLimits'],
                'symbols': [{
                    'symbol': s['symbol'],
                    'status': s['status'],
                    'base_asset': s['baseAsset'],
                    'quote_asset': s['quoteAsset'],
                    'min_price': float(s['filters'][0]['minPrice']),
                    'max_price': float(s['filters'][0]['maxPrice']),
                    'tick_size': float(s['filters'][0]['tickSize']),
                    'min_qty': float(s['filters'][1]['minQty']),
                    'max_qty': float(s['filters'][1]['maxQty']),
                    'step_size': float(s['filters'][1]['stepSize']),
                    'min_notional': float(s['filters'][2]['minNotional'])
                } for s in info['symbols']]
            }
        except BinanceAPIException as e:
            self.handle_error(e)
        except Exception as e:
            logger.error(f"Error getting exchange info: {str(e)}")
            raise ExchangeAPIError(f"Failed to get exchange info: {str(e)}")

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