from fastapi import APIRouter, HTTPException, Depends, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import schemas, crud
from ..database import get_db
from ..exchanges.factory import ExchangeClientFactory
from ..utils.exceptions import ExchangeAPIError
from ..utils.customLogger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/bybit/spot",
    tags=["bybit-spot"],
    responses={404: {"description": "Not found"}}
)

def get_bybit_spot_client(account_id: int, db: Session):
    """Get Bybit spot client for given account"""
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
            exchange=schemas.ExchangeType.BYBIT,
            market_type=schemas.MarketType.SPOT,
            api_key=account.api_key,
            api_secret=account.api_secret,
            testnet=account.is_testnet
        )
    except Exception as e:
        logger.error(f"Failed to create Bybit spot client: {str(e)}")
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
    client = get_bybit_spot_client(account_id, db)
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
    client = get_bybit_spot_client(account_id, db)
    try:
        return client.get_balance(asset)
    except ExchangeAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.post("/order", response_model=schemas.OrderResponse)
async def create_order(
    order: schemas.CreateOrderRequest,
    account_id: int = Query(..., description="Trading account ID"),
    db: Session = Depends(get_db)
):
    """Create a new order"""
    client = get_bybit_spot_client(account_id, db)
    try:
        response = client.create_order(
            symbol=order.symbol,
            side=order.side.value,
            order_type=order.type.value,
            quantity=order.quantity,
            price=order.price
        )
        
        # Save order to database
        trade_data = schemas.TradeCreate(
            trading_account_id=account_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=float(response['price']) if response['price'] else 0,
            type=order.type,
            order_id=response['order_id']
        )
        crud.create_trade(db, trade_data)
        
        return response
    except ExchangeAPIError as e:
        raise HTTPException(status_code=502, detail=str(e)) 