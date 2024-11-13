from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from ..utils.exceptions import ExchangeAPIError
from ..utils.customLogger import get_logger

logger = get_logger(__name__)

class ExchangeClientBase(ABC):
    """Abstract base class for all exchange clients"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
    @abstractmethod
    def get_account(self) -> Dict:
        """Get account information"""
        pass
        
    @abstractmethod
    def get_balance(self, asset: Optional[str] = None) -> Dict:
        """Get account balance"""
        pass
        
    @abstractmethod
    def get_symbol_price(self, symbol: str) -> Dict:
        """Get current price for a symbol"""
        pass
        
    @abstractmethod
    def create_order(self, symbol: str, side: str, order_type: str, quantity: float, price: Optional[float] = None) -> Dict:
        """Create a new order"""
        pass
        
    @abstractmethod
    def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """Cancel an existing order"""
        pass
        
    @abstractmethod
    def get_order(self, symbol: str, order_id: str) -> Dict:
        """Get order details"""
        pass
        
    @abstractmethod
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all open orders"""
        pass
        
    @abstractmethod
    def get_order_history(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get order history"""
        pass

    def handle_error(self, error: Exception) -> None:
        """Handle exchange-specific errors"""
        error_msg = f"Exchange API Error: {str(error)}"
        logger.error(error_msg)
        raise ExchangeAPIError(error_msg) 
        # 