from typing import Optional
from decimal import Decimal
from ..utils.exceptions import ValidationError

def validate_leverage(leverage: int) -> None:
    """
    Validate leverage value for Binance Futures
    
    Args:
        leverage (int): Leverage value to validate
        
    Raises:
        ValidationError: If leverage is invalid
    """
    if not isinstance(leverage, int):
        raise ValidationError("Leverage must be an integer")
    if leverage < 1 or leverage > 125:
        raise ValidationError("Leverage must be between 1 and 125")

def validate_quantity(
    quantity: float,
    min_qty: Optional[float] = None,
    max_qty: Optional[float] = None
) -> None:
    """
    Validate order quantity
    
    Args:
        quantity (float): Quantity to validate
        min_qty (float, optional): Minimum allowed quantity
        max_qty (float, optional): Maximum allowed quantity
        
    Raises:
        ValidationError: If quantity is invalid
    """
    if quantity <= 0:
        raise ValidationError("Quantity must be greater than 0")
    if min_qty and quantity < min_qty:
        raise ValidationError(f"Quantity must be greater than {min_qty}")
    if max_qty and quantity > max_qty:
        raise ValidationError(f"Quantity must be less than {max_qty}")

def validate_price(
    price: float,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
) -> None:
    """
    Validate order price
    
    Args:
        price (float): Price to validate
        min_price (float, optional): Minimum allowed price
        max_price (float, optional): Maximum allowed price
        
    Raises:
        ValidationError: If price is invalid
    """
    if price <= 0:
        raise ValidationError("Price must be greater than 0")
    if min_price and price < min_price:
        raise ValidationError(f"Price must be greater than {min_price}")
    if max_price and price > max_price:
        raise ValidationError(f"Price must be less than {max_price}")

def validate_symbol(symbol: str) -> None:
    """
    Validate trading symbol format
    
    Args:
        symbol (str): Symbol to validate
        
    Raises:
        ValidationError: If symbol format is invalid
    """
    if not isinstance(symbol, str):
        raise ValidationError("Symbol must be a string")
    if not symbol.isupper():
        raise ValidationError("Symbol must be uppercase")
    if len(symbol) < 5:  # Minimum length for valid trading pair
        raise ValidationError("Invalid symbol format")
    if not symbol.endswith('USDT'):
        raise ValidationError("Symbol must end with USDT")
 