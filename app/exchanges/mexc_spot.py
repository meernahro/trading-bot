from typing import Dict, Optional, List
from mexc_sdk import Spot
from .base import ExchangeClientBase
from ..utils.exceptions import ExchangeAPIError
from ..utils.customLogger import get_logger
from fastapi import HTTPException

logger = get_logger(__name__)

class MEXCSpotClient(ExchangeClientBase):
    """MEXC Spot Exchange Client"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        super().__init__(api_key, api_secret, testnet)
        try:
            # Initialize MEXC SDK client
            self.client = Spot(
                api_key=api_key,
                api_secret=api_secret
            )
            
            # Test connection using ping and time
            self.client.ping()
            self.client.time()
            
            # Log testnet warning since MEXC doesn't have a proper testnet
            if testnet:
                logger.warning("MEXC does not provide a testnet. Using mainnet with test API keys.")
            
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
                'symbol': symbol,
                'price': float(ticker['price']),
                'timestamp': int(ticker.get('timestamp', 0))
            }
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
        **kwargs
    ) -> Dict:
        """Create a new order
        
        Args:
            symbol: Trading pair
            side: BUY or SELL
            order_type: LIMIT or MARKET
            quantity: Amount of base asset to trade
            price: Price for limit orders
            quote_order_qty: Amount of quote asset (USDT) to spend (only for BUY orders)
        """
        # Build options dictionary
        options = {}
        
        if order_type.upper() == 'MARKET':
            if quote_order_qty and side.upper() == 'BUY':
                options['quoteOrderQty'] = quote_order_qty
            if quantity:
                options['quantity'] = quantity
            
        elif order_type.upper() == 'LIMIT':
            options['quantity'] = quantity
            options['price'] = price
            options['timeInForce'] = kwargs.get('time_in_force', 'GTC')

        # Add any additional parameters from kwargs
        for key, value in kwargs.items():
            if value is not None:
                options[key] = value

        logger.info(f"Creating MEXC order: symbol={symbol}, side={side}, type={order_type}")
        logger.debug(f"Order options: {options}")

        try:
            # Always request FULL response type
            options['newOrderRespType'] = 'FULL'
            
            order = self.client.new_order(
                symbol=symbol,
                side=side.upper(),
                order_type=order_type.upper(),
                options=options
            )
            
            logger.info(f"MEXC order created successfully: {order.get('orderId', 'N/A')}")
            logger.debug(f"Full order response: {order}")
            
            try:
                formatted_order = self._format_order(order)
                logger.debug(f"Formatted order: {formatted_order}")
                return formatted_order
            except KeyError as e:
                logger.error(f"Failed to format order response: {str(e)}")
                # Return the raw order response if formatting fails
                return order
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating order: {error_msg}")
            
            # Look for JSON in the error message
            try:
                import json
                # Try to find JSON after the status code line
                if "status code 400:" in error_msg:
                    json_str = error_msg.split("status code 400:", 1)[1].strip()
                    mexc_error = json.loads(json_str)
                # Or try the original method
                elif '{"code":' in error_msg:
                    json_str = error_msg[error_msg.find('{'):error_msg.rfind('}')+1]
                    mexc_error = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in error message")
                
                raise HTTPException(
                    status_code=400,
                    detail=mexc_error
                )
                
            except (json.JSONDecodeError, ValueError):
                # If we can't parse the JSON, return the original error
                raise HTTPException(
                    status_code=400,
                    detail={"message": error_msg}
                )

    def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """Cancel an existing order"""
        try:
            order = self.client.cancel_order(symbol=symbol, orderId=order_id)
            return self._format_order(order)
        except Exception as e:
            logger.error(f"Error canceling order: {str(e)}")
            raise ExchangeAPIError(f"Failed to cancel order: {str(e)}")

    def get_order(self, symbol: str, order_id: str) -> Dict:
        """Get order details"""
        try:
            order = self.client.get_order(symbol=symbol, orderId=order_id)
            return self._format_order(order)
        except Exception as e:
            logger.error(f"Error getting order: {str(e)}")
            raise ExchangeAPIError(f"Failed to get order: {str(e)}")

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all open orders"""
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol
            orders = self.client.open_orders(**params)
            return [self._format_order(order) for order in orders]
        except Exception as e:
            logger.error(f"Error getting open orders: {str(e)}")
            raise ExchangeAPIError(f"Failed to get open orders: {str(e)}")

    def get_order_book(self, symbol: str, limit: int = 100) -> Dict:
        """Get order book for a symbol"""
        try:
            depth = self.client.depth(symbol=symbol, limit=limit)
            return {
                'symbol': symbol,
                'bids': [[float(price), float(qty)] for price, qty in depth['bids']],
                'asks': [[float(price), float(qty)] for price, qty in depth['asks']],
                'timestamp': int(depth.get('timestamp', 0))
            }
        except Exception as e:
            logger.error(f"Error getting order book: {str(e)}")
            raise ExchangeAPIError(f"Failed to get order book: {str(e)}")

    def _format_order(self, order: Dict) -> Dict:
        """Format order response to standardized format"""
        return {
            'order_id': str(order['orderId']),
            'symbol': order['symbol'],
            'status': order.get('status', 'FILLED'),
            'side': order['side'],
            'type': order['type'],
            'price': float(order['price']),
            'quantity': float(order['origQty']),
            'executed_qty': float(order.get('executedQty', order['origQty'])),
            'cummulative_quote_qty': float(order.get('cummulativeQuoteQty', 0)),
            'time': order.get('transactTime', order.get('time', 0)),
            'update_time': order.get('updateTime', order.get('transactTime', order.get('time', 0)))
        }

    def get_server_time(self) -> Dict:
        """Get MEXC server time"""
        try:
            return self.client.time()
        except Exception as e:
            logger.error(f"Error getting server time: {str(e)}")
            raise ExchangeAPIError(f"Failed to get server time: {str(e)}")

    def test_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        **kwargs
    ) -> Dict:
        """Test new order creation without actually placing it"""
        try:
            # Build options dictionary
            options = {
                'quantity': quantity
            }
            
            if order_type.upper() == 'LIMIT':
                if not price:
                    raise ValueError("Price is required for LIMIT orders")
                options['price'] = price
                options['timeInForce'] = kwargs.get('time_in_force', 'GTC')

            # Add any additional parameters from kwargs
            for key, value in kwargs.items():
                if value is not None:
                    options[key] = value

            logger.info(f"Testing MEXC order: symbol={symbol}, side={side}, type={order_type}")
            logger.debug(f"Test order options: {options}")

            # Use the test order endpoint with options parameter
            response = self.client.new_order_test(
                symbol=symbol,
                side=side.upper(),
                order_type=order_type.upper(),
                options=options
            )
            
            logger.info("MEXC order test completed successfully")
            logger.debug(f"Test response: {response}")
            
            result = {
                'test': True,
                'valid': True,
                'message': 'Order validation successful',
                'params': {
                    'symbol': symbol,
                    'side': side,
                    'order_type': order_type,
                    **options
                }
            }
            
            logger.debug(f"Formatted test result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error testing order: {str(e)}")
            raise ExchangeAPIError(f"Failed to test order: {str(e)}")

    def get_order_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 500,
        from_id: Optional[str] = None
    ) -> List[Dict]:
        """Get historical orders"""
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol
            if limit:
                params['limit'] = min(limit, 1000)  # MEXC max limit is 1000
            if from_id:
                params['fromId'] = from_id

            orders = self.client.all_orders(**params)
            return [self._format_order(order) for order in orders]
        except Exception as e:
            logger.error(f"Error getting order history: {str(e)}")
            raise ExchangeAPIError(f"Failed to get order history: {str(e)}")