# app/binanceClient.py

from binance.client import Client
from binance.exceptions import BinanceAPIException
from .utils.customLogger import get_logger
from .utils.exceptions import BinanceAPIError
from typing import Optional, List, Dict

logger = get_logger(name="binance_client")

class BinanceClient:
    def __init__(self, api_key: str, api_secret: str, environment: str = 'development'):
        self.client = Client(api_key, api_secret)
        self.setup_environment(environment)
        
    def setup_environment(self, environment: str):
        """Configure API URLs based on environment"""
        if environment.lower() == 'development':
            logger.info("Running in development mode - using testnet")
            self.client.API_URL = 'https://testnet.binance.vision/api'
            self.client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'
        else:
            logger.info("Running in production mode - using live API")
            self.client.API_URL = 'https://api.binance.com/api'
            self.client.FUTURES_URL = 'https://fapi.binance.com/fapi'

    def futures_position_information(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get position information"""
        try:
            try:
                if symbol:
                    response = self.client.futures_position_information(symbol=symbol)
                else:
                    response = self.client.futures_position_information()
                    
                # Ensure response is properly formatted
                if not isinstance(response, list):
                    raise BinanceAPIError("Invalid response format from Binance API")
                    
                # Convert all numeric strings to float
                for pos in response:
                    for key in ['positionAmt', 'entryPrice', 'markPrice', 'unRealizedProfit', 'liquidationPrice']:
                        if key in pos:
                            try:
                                pos[key] = float(pos[key])
                            except (ValueError, TypeError):
                                pos[key] = 0.0
                                
                return response
                
            except BinanceAPIException as e:
                if "No such symbol" in str(e):
                    return []
                raise e
                
        except BinanceAPIException as e:
            self.handle_binance_error(e)
        except Exception as e:
            logger.error(f"Error getting position information: {str(e)}")
            raise BinanceAPIError(f"Failed to get position information: {str(e)}")

    def futures_change_leverage(self, symbol: str, leverage: int) -> dict:
        """Change leverage for a symbol"""
        try:
            response = self.client.futures_change_leverage(
                symbol=symbol,
                leverage=leverage
            )
            logger.info(f"Changed leverage for {symbol} to {leverage}x")
            return response
        except BinanceAPIException as e:
            self.handle_binance_error(e)
        except Exception as e:
            logger.error(f"Error changing leverage: {str(e)}")
            raise BinanceAPIError(f"Failed to change leverage: {str(e)}")

    def futures_create_order(self, **kwargs) -> dict:
        """Create a futures order with error handling"""
        try:
            response = self.client.futures_create_order(**kwargs)
            logger.info(f"Created futures order: {kwargs.get('symbol')} {kwargs.get('side')} {kwargs.get('type')}")
            return response
        except BinanceAPIException as e:
            self.handle_binance_error(e)
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            raise BinanceAPIError(f"Failed to create order: {str(e)}")

    def futures_account(self) -> dict:
        """Get futures account information"""
        try:
            return self.client.futures_account()
        except BinanceAPIException as e:
            self.handle_binance_error(e)
        except Exception as e:
            logger.error(f"Error getting account information: {str(e)}")
            raise BinanceAPIError(f"Failed to get account information: {str(e)}")

    def handle_binance_error(self, error: BinanceAPIException):
        """Handle Binance API errors with proper logging"""
        error_msg = f"Binance API Error: {error.code} - {error.message}"
        logger.error(error_msg)
        raise BinanceAPIError(error_msg)

    def futures_mark_price(self, symbol: str) -> dict:
        """Get mark price for a symbol"""
        try:
            response = self.client.futures_mark_price(symbol=symbol)
            return response
        except BinanceAPIException as e:
            self.handle_binance_error(e)
        except Exception as e:
            logger.error(f"Error getting mark price: {str(e)}")
            raise BinanceAPIError(f"Failed to get mark price: {str(e)}")

def create_client(api_key: str, api_secret: str, environment: str = 'development') -> BinanceClient:
    """Create a new BinanceClient instance"""
    return BinanceClient(api_key, api_secret, environment)
