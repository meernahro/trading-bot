from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from decimal import Decimal
from .. import schemas, crud
from ..database import get_db
from ..utils.exceptions import DatabaseError, BinanceAPIError
from ..utils.customLogger import get_logger
from ..binanceClient import create_client
from ..config import ENVIRONMENT

logger = get_logger(name="binance_futures")
router = APIRouter(
    prefix="/binance/futures",
    tags=["binance_futures"],
    responses={
        401: {"model": schemas.HTTPError, "description": "Unauthorized"},
        403: {"model": schemas.HTTPError, "description": "Forbidden"},
        404: {"model": schemas.HTTPError, "description": "Not Found"},
        500: {"model": schemas.HTTPError, "description": "Internal Server Error"},
        502: {"model": schemas.HTTPError, "description": "Binance API Error"}
    }
)

@router.post("/position/open", response_model=schemas.OrderResponse)
async def open_position(
    order: schemas.OpenPositionRequest,
    account_id: int = Query(..., description="Trading account ID"),
    db: Session = Depends(get_db)
):
    """Open a new futures position"""
    try:
        # Get trading account
        account = crud.get_trading_account(db, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Trading account not found")
        
        if account.status != schemas.AccountStatus.ACTIVE:
            raise HTTPException(
                status_code=403, 
                detail="Trading account is not active"
            )
            
        # Create Binance client
        try:
            client = create_client(
                account.api_key,
                account.api_secret,
                ENVIRONMENT if not account.is_testnet else 'development'
            )
        except Exception as e:
            raise BinanceAPIError(f"Failed to connect to Binance: {str(e)}")
        
        try:
            # Set leverage
            client.futures_change_leverage(
                symbol=order.symbol,
                leverage=order.leverage
            )
            
            # Place order
            response = client.futures_create_order(
                symbol=order.symbol,
                side='BUY' if order.side == schemas.OrderSide.LONG else 'SELL',
                type=order.type.value,
                quantity=order.quantity,
                price=order.price if order.type == schemas.OrderType.LIMIT else None,
                timeInForce='GTC' if order.type == schemas.OrderType.LIMIT else None
            )
            
            # Save trade to database
            trade_data = schemas.TradeCreate(
                trading_account_id=account_id,
                symbol=order.symbol,
                side=order.side.value,
                quantity=order.quantity,
                price=float(response['avgPrice']) if 'avgPrice' in response else float(order.price or 0),
                type=order.type,
                leverage=order.leverage,
                order_id=str(response['orderId'])
            )
            crud.create_trade(db, trade_data)
            
            return {"status": "success", "order": response}
            
        except Exception as e:
            raise BinanceAPIError(str(e))
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error opening position: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/position/close", response_model=schemas.OrderResponse)
async def close_position(
    order: schemas.ClosePositionRequest,
    account_id: int = Query(..., description="Trading account ID"),
    db: Session = Depends(get_db)
):
    """Close an existing futures position"""
    try:
        account = crud.get_trading_account(db, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Trading account not found")
            
        if account.status != schemas.AccountStatus.ACTIVE:
            raise HTTPException(
                status_code=403, 
                detail="Trading account is not active"
            )
            
        try:
            client = create_client(
                account.api_key,
                account.api_secret,
                ENVIRONMENT if not account.is_testnet else 'development'
            )
        except Exception as e:
            raise BinanceAPIError(f"Failed to connect to Binance: {str(e)}")
        
        try:
            response = client.futures_create_order(
                symbol=order.symbol,
                side='SELL' if order.side == schemas.OrderSide.LONG else 'BUY',  # Reverse side for closing
                type=order.type.value,
                quantity=order.quantity,
                price=order.price if order.type == schemas.OrderType.LIMIT else None,
                timeInForce='GTC' if order.type == schemas.OrderType.LIMIT else None,
                reduceOnly=True
            )
            
            # Save trade to database
            trade_data = schemas.TradeCreate(
                trading_account_id=account_id,
                symbol=order.symbol,
                side=f"CLOSE_{order.side.value}",
                quantity=order.quantity,
                price=float(response['avgPrice']) if 'avgPrice' in response else float(order.price or 0),
                type=order.type,
                reduce_only=True,
                order_id=str(response['orderId'])
            )
            crud.create_trade(db, trade_data)
            
            return {"status": "success", "order": response}
            
        except Exception as e:
            raise BinanceAPIError(str(e))
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error closing position: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/positions", response_model=schemas.PositionsResponse)
async def get_positions(
    account_id: int = Query(..., description="Trading account ID"),
    symbol: Optional[str] = Query(None, description="Symbol to get position for"),
    db: Session = Depends(get_db)
):
    """Get futures positions"""
    try:
        account = crud.get_trading_account(db, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Trading account not found")
            
        if account.status != schemas.AccountStatus.ACTIVE:
            raise HTTPException(
                status_code=403, 
                detail="Trading account is not active"
            )
            
        try:
            client = create_client(
                account.api_key,
                account.api_secret,
                ENVIRONMENT if not account.is_testnet else 'development'
            )
        except Exception as e:
            raise BinanceAPIError(f"Failed to connect to Binance: {str(e)}")
        
        try:
            positions = client.futures_position_information(symbol=symbol)
            
            # Filter out positions with zero amount
            positions = [
                pos for pos in positions 
                if float(pos.get('positionAmt', 0)) != 0
            ]
            
            return {"status": "success", "positions": positions}
            
        except Exception as e:
            logger.error(f"Error fetching positions: {str(e)}")
            raise BinanceAPIError(str(e))
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in get_positions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/account", response_model=schemas.FuturesAccountResponse)
async def get_account_info(
    account_id: int = Query(..., description="Trading account ID"),
    db: Session = Depends(get_db)
):
    """Get futures account information"""
    try:
        account = crud.get_trading_account(db, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Trading account not found")
            
        if account.status != schemas.AccountStatus.ACTIVE:
            raise HTTPException(
                status_code=403, 
                detail="Trading account is not active"
            )
            
        try:
            client = create_client(
                account.api_key,
                account.api_secret,
                ENVIRONMENT if not account.is_testnet else 'development'
            )
        except Exception as e:
            raise BinanceAPIError(f"Failed to connect to Binance: {str(e)}")
        
        try:
            account_info = client.futures_account()
            return {"status": "success", "account": account_info}
            
        except Exception as e:
            raise BinanceAPIError(str(e))
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching account info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/leverage", response_model=schemas.LeverageResponse)
async def change_leverage(
    leverage_request: schemas.LeverageRequest,
    account_id: int = Query(..., description="Trading account ID"),
    db: Session = Depends(get_db)
):
    """Change leverage for a symbol"""
    try:
        account = crud.get_trading_account(db, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Trading account not found")
            
        if account.status != schemas.AccountStatus.ACTIVE:
            raise HTTPException(
                status_code=403, 
                detail="Trading account is not active"
            )
            
        try:
            client = create_client(
                account.api_key,
                account.api_secret,
                ENVIRONMENT if not account.is_testnet else 'development'
            )
        except Exception as e:
            raise BinanceAPIError(f"Failed to connect to Binance: {str(e)}")
        
        try:
            response = client.futures_change_leverage(
                symbol=leverage_request.symbol,
                leverage=leverage_request.leverage
            )
            return {"status": "success", "leverage": response}
            
        except Exception as e:
            raise BinanceAPIError(str(e))
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error changing leverage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/price", response_model=schemas.PriceResponse)
async def get_symbol_price(
    symbol: str = Query(..., description="Trading symbol"),
    account_id: int = Query(..., description="Trading account ID"),
    db: Session = Depends(get_db)
):
    """Get current price for a symbol"""
    try:
        account = crud.get_trading_account(db, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Trading account not found")
            
        client = create_client(
            account.api_key,
            account.api_secret,
            ENVIRONMENT if not account.is_testnet else 'development'
        )
        
        try:
            price_info = client.futures_mark_price(symbol=symbol)
            return {"price": price_info["markPrice"]}
            
        except Exception as e:
            raise BinanceAPIError(str(e))
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting price: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )