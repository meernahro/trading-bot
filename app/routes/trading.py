# app/routes/trading.py

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db
from ..utils.exceptions import DatabaseError, UserNotFoundError, InvalidCredentialsError, BinanceAPIError
from ..utils.customLogger import get_logger
from ..binanceClient import create_client
from ..config import WEBHOOK_PASSPHRASE, ENVIRONMENT

logger = get_logger(name="trading")
router = APIRouter(prefix="/trading", tags=["trading"])

@router.post("/webhook", response_model=schemas.WebhookResponseModel)
async def webhook(payload: schemas.WebhookPayload, db: Session = Depends(get_db)):
    try:
        if payload.passphrase != WEBHOOK_PASSPHRASE:
            raise InvalidCredentialsError()

        # Get the trading account
        account = crud.get_trading_account(db, payload.account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trading account {payload.account_id} not found"
            )
        
        # Verify account status
        if account.status != schemas.AccountStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Trading account {payload.account_id} is not active"
            )
        
        try:
            client = create_client(
                account.api_key, 
                account.api_secret, 
                ENVIRONMENT if not account.is_testnet else 'development'
            )
        except Exception as e:
            raise BinanceAPIError(f"Failed to create Binance client: {str(e)}")

        try:
            # Set leverage
            client.futures_change_leverage(symbol=payload.symbol, leverage=payload.leverage)
            
            # Prepare order parameters
            action = payload.action.lower()
            symbol = payload.symbol.upper()
            quantity = payload.quantity
            price = payload.price
            order_type = 'LIMIT' if price != "market" else 'MARKET'

            if action == "open_long":
                side = 'BUY'
                reduce_only = False
            elif action == "open_short":
                side = 'SELL'
                reduce_only = False
            elif action == "close_long":
                side = 'SELL'
                reduce_only = True
            elif action == "close_short":
                side = 'BUY'
                reduce_only = True
            else:
                raise HTTPException(status_code=400, detail=f"Invalid action: {action}")

            # Place the order
            order = client.futures_create_order(
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity,
                price=price if order_type == 'LIMIT' else None,
                reduceOnly=reduce_only,
                timeInForce='GTC' if order_type == 'LIMIT' else None
            )

            # Save the trade to database
            trade_data = schemas.TradeCreate(
                trading_account_id=account.id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=float(order['price']),
                type=order_type,
                reduce_only=reduce_only,
                leverage=payload.leverage
            )
            crud.create_trade(db, trade_data)

            return {"status": "success", "order": order}

        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
