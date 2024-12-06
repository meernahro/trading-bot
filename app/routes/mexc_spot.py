from fastapi import APIRouter, HTTPException, Depends, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import schemas, crud
from ..database import get_db
from ..exchanges.factory import ExchangeClientFactory
from ..utils.exceptions import ExchangeAPIError
from ..utils.customLogger import get_logger
from ..utils.validation import validate_symbol
from pydantic import ValidationError

logger = get_logger(__name__)

router = APIRouter(
    prefix="/mexc/spot",
    tags=["mexc-spot"],
    responses={404: {"description": "Not found"}}
)

def get_mexc_spot_client(account_id: int, db: Session):
    """Get MEXC spot client for given account"""
    account = crud.get_trading_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Trading account not found")
        
    if account.status != schemas.AccountStatus.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail="Trading account is not active"
        )
        
    try:
        return ExchangeClientFactory.create_client(
            exchange=schemas.ExchangeType.MEXC,
            market_type=schemas.MarketType.SPOT,
            api_key=account.api_key,
            api_secret=account.api_secret,
            testnet=account.is_testnet
        )
    except Exception as e:
        logger.error(f"Failed to create MEXC spot client: {str(e)}")
        raise HTTPException(
            status_code=402,
            detail=f"Failed to initialize exchange client: {str(e)}"
        )

@router.get("/{account_id}/account")
def get_account(
    account_id: int,
    db: Session = Depends(get_db)
):
    """Get MEXC account information"""
    client = get_mexc_spot_client(account_id, db)
    try:
        return client.get_account()
    except ExchangeAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.get("/{account_id}/balance")
def get_balance(
    account_id: int,
    asset: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get account balance"""
    client = get_mexc_spot_client(account_id, db)
    try:
        return client.get_balance(asset)
    except ExchangeAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.get("/{account_id}/price/{symbol}")
def get_symbol_price(
    account_id: int,
    symbol: str,
    db: Session = Depends(get_db)
):
    """Get current price for a symbol"""
    client = get_mexc_spot_client(account_id, db)
    try:
        return client.get_symbol_price(symbol)
    except ExchangeAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.post("/{account_id}/order",
    responses={
        400: {"description": "Bad Request"},
        404: {"description": "Trading account not found"},
        403: {"description": "Trading account is not active"},
        402: {"description": "Failed to initialize exchange client"},
        422: {"description": "Validation Error"},
        502: {"description": "Exchange API Error"}
    }
)
def create_order(
    account_id: int,
    order: schemas.MEXCOrderCreate,
    db: Session = Depends(get_db)
):
    """Create a new order
    
    You can create orders in two ways:
    1. Specify quantity: Amount of base asset to trade
    2. Specify quote_order_qty: Amount of USDT to spend (only for BUY orders)
    """
    # Let any exceptions from get_mexc_spot_client propagate up
    client = get_mexc_spot_client(account_id, db)
    
    # Build parameters dict with only provided values
    params = {
        'symbol': order.symbol,
        'side': order.side,
        'order_type': order.type
    }

    # Add optional parameters only if they are provided
    if order.quantity is not None:
        params['quantity'] = order.quantity
    if order.price is not None:
        params['price'] = order.price
    if order.quote_order_qty is not None:
        params['quote_order_qty'] = order.quote_order_qty

    # Let any exceptions from create_order propagate up
    return client.create_order(**params)

@router.delete("/{account_id}/order/{symbol}/{order_id}")
def cancel_order(
    account_id: int,
    symbol: str,
    order_id: str,
    db: Session = Depends(get_db)
):
    """Cancel an existing order"""
    client = get_mexc_spot_client(account_id, db)
    try:
        return client.cancel_order(symbol=symbol, order_id=order_id)
    except ExchangeAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.get("/{account_id}/order/{symbol}/{order_id}")
def get_order(
    account_id: int,
    symbol: str,
    order_id: str,
    db: Session = Depends(get_db)
):
    """Get order details"""
    client = get_mexc_spot_client(account_id, db)
    try:
        return client.get_order(symbol=symbol, order_id=order_id)
    except ExchangeAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.get("/{account_id}/open-orders")
def get_open_orders(
    account_id: int,
    symbol: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all open orders"""
    client = get_mexc_spot_client(account_id, db)
    try:
        return client.get_open_orders(symbol)
    except ExchangeAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.get("/{account_id}/orderbook/{symbol}")
def get_order_book(
    account_id: int,
    symbol: str,
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """Get order book for a symbol"""
    client = get_mexc_spot_client(account_id, db)
    try:
        return client.get_order_book(symbol, limit)
    except ExchangeAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.post("/{account_id}/order/test")
def test_order(
    account_id: int,
    order: schemas.MEXCOrderTest,
    db: Session = Depends(get_db)
):
    """Test new order parameters without creating an actual order"""
    client = get_mexc_spot_client(account_id, db)
    try:
        # Extract optional parameters
        kwargs = {
            'time_in_force': order.time_in_force,
            'quote_order_qty': order.quote_order_qty,
            'stop_price': order.stop_price,
            'iceberg_qty': order.iceberg_qty
        }
        # Remove None values
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        
        return client.test_order(
            symbol=order.symbol,
            side=order.side,
            order_type=order.type,
            quantity=order.quantity,
            price=order.price,
            **kwargs
        )
    except ExchangeAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.get("/{account_id}/orders")
def get_order_history(
    account_id: int,
    symbol: Optional[str] = None,
    limit: int = Query(500, le=1000),
    from_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get historical orders"""
    client = get_mexc_spot_client(account_id, db)
    try:
        return client.get_order_history(
            symbol=symbol,
            limit=limit,
            from_id=from_id
        )
    except ExchangeAPIError as e:
        raise HTTPException(status_code=502, detail=str(e)) 