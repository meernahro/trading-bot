from fastapi import APIRouter, HTTPException, Depends, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from .. import schemas, crud
from ..database import get_db
from ..exchanges.factory import ExchangeClientFactory
from ..utils.exceptions import ExchangeAPIError
from ..utils.customLogger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/binance/spot",
    tags=["binance-spot"],
    responses={404: {"description": "Not found"}}
)

def get_binance_spot_client(account_id: int, db: Session):
    """Get Binance spot client for given account"""
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
            exchange=schemas.ExchangeType.BINANCE,
            market_type=schemas.MarketType.SPOT,
            api_key=account.api_key,
            api_secret=account.api_secret,
            testnet=account.is_testnet
        )
    except Exception as e:
        logger.error(f"Failed to create Binance spot client: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize exchange client: {str(e)}"
        )

@router.get("/account")
async def get_account_info(
    account_id: int = Query(..., description="Trading account ID"),
    db: Session = Depends(get_db)
):
    """Get account information"""
    client = get_binance_spot_client(account_id, db)
    try:
        return client.get_account()
    except ExchangeAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.get("/balance/{asset}")
async def get_asset_balance(
    asset: str,
    account_id: int = Query(..., description="Trading account ID"),
    db: Session = Depends(get_db)
):
    """Get balance for specific asset"""
    client = get_binance_spot_client(account_id, db)
    try:
        return client.get_balance(asset)
    except ExchangeAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.post("/order", response_model=schemas.OrderResponse)
async def create_order(
    order: schemas.BinanceSpotOrderRequest,
    account_id: int = Query(..., description="Trading account ID"),
    db: Session = Depends(get_db)
):
    """Create a new order"""
    client = get_binance_spot_client(account_id, db)
    try:
        if order.type == schemas.BinanceOrderType.MARKET:
            params = {
                'symbol': order.market_order.symbol,
                'side': order.market_order.side.value,
                'order_type': order.type.value
            }
            
            # Handle market orders with either quantity or quote_order_qty
            if order.market_order.quoteOrderQty is not None:
                params['quote_order_qty'] = order.market_order.quoteOrderQty
            else:
                params['quantity'] = order.market_order.quantity
                
        else:  # LIMIT order
            params = {
                'symbol': order.limit_order.symbol,
                'side': order.limit_order.side.value,
                'order_type': order.type.value,
                'quantity': order.limit_order.quantity,
                'price': order.limit_order.price,
                'time_in_force': order.limit_order.timeInForce.value
            }

        response = client.create_order(**params)
        
        # Save order to database
        trade_data = schemas.TradeCreate(
            trading_account_id=account_id,
            symbol=order.market_order.symbol if order.type == schemas.BinanceOrderType.MARKET else order.limit_order.symbol,
            side=order.market_order.side if order.type == schemas.BinanceOrderType.MARKET else order.limit_order.side,
            quantity=float(response['executed_qty']),
            price=float(response['price']) if response['price'] else 0,
            type=order.type,
            order_id=response['order_id']
        )
        crud.create_trade(db, trade_data)
        
        return response
    except ExchangeAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.get("/orderbook/{symbol}")
async def get_order_book(
    symbol: str = Path(..., description="Trading symbol"),
    limit: int = Query(100, le=1000, description="Number of orders to return"),
    account_id: int = Query(..., description="Trading account ID"),
    db: Session = Depends(get_db)
):
    """Get order book for a symbol"""
    client = get_binance_spot_client(account_id, db)
    try:
        return client.get_order_book(symbol=symbol, limit=limit)
    except ExchangeAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.get("/trades/{symbol}")
async def get_recent_trades(
    symbol: str = Path(..., description="Trading symbol"),
    limit: int = Query(50, le=1000, description="Number of trades to return"),
    account_id: int = Query(..., description="Trading account ID"),
    db: Session = Depends(get_db)
):
    """Get recent trades for a symbol"""
    client = get_binance_spot_client(account_id, db)
    try:
        return client.get_recent_trades(symbol=symbol, limit=limit)
    except ExchangeAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.get("/klines/{symbol}")
async def get_klines(
    symbol: str = Path(..., description="Trading symbol"),
    interval: str = Query(..., description="Kline interval (1m, 5m, 15m, 1h, etc.)"),
    limit: int = Query(500, le=1000, description="Number of klines to return"),
    account_id: int = Query(..., description="Trading account ID"),
    db: Session = Depends(get_db)
):
    """Get klines/candlestick data"""
    client = get_binance_spot_client(account_id, db)
    try:
        return client.get_klines(symbol=symbol, interval=interval, limit=limit)
    except ExchangeAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.get("/ticker/{symbol}")
async def get_24h_ticker(
    symbol: str = Path(..., description="Trading symbol"),
    account_id: int = Query(..., description="Trading account ID"),
    db: Session = Depends(get_db)
):
    """Get 24-hour ticker statistics"""
    client = get_binance_spot_client(account_id, db)
    try:
        return client.get_24h_ticker(symbol=symbol)
    except ExchangeAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.get("/exchange-info")
async def get_exchange_info(
    account_id: int = Query(..., description="Trading account ID"),
    db: Session = Depends(get_db)
):
    """Get exchange trading rules and symbol information"""
    client = get_binance_spot_client(account_id, db)
    try:
        return client.get_exchange_info()
    except ExchangeAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.get("/orders/{symbol}")
async def get_symbol_orders(
    symbol: str = Path(..., description="Trading symbol"),
    status: Optional[str] = Query(None, description="Order status (open, closed, all)"),
    limit: int = Query(50, le=500, description="Number of orders to return"),
    account_id: int = Query(..., description="Trading account ID"),
    db: Session = Depends(get_db)
):
    """Get orders for a symbol"""
    client = get_binance_spot_client(account_id, db)
    try:
        if status == "open":
            orders = client.get_open_orders(symbol=symbol)
        elif status == "all":
            orders = client.get_order_history(symbol=symbol)
        else:
            orders = []
        return orders[:limit]
    except ExchangeAPIError as e:
        raise HTTPException(status_code=502, detail=str(e)) 