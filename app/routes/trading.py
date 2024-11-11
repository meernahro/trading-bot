# app/routes/trading.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import SessionLocal
from ..config import WEBHOOK_PASSPHRASE
from ..utils.customLogger import get_logger
from ..binanceClient import create_client
from ..config import ENVIRONMENT
from ..utils.exceptions import (
    DatabaseError,
    UserNotFoundError,
    InvalidCredentialsError,
    BinanceAPIError
)
from datetime import datetime
from ..models import Trade

logging = get_logger(name="trading")
router = APIRouter()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/webhook", tags=["trading"], summary="Execute a trading action", response_model=schemas.WebhookResponseModel)
async def webhook(payload: schemas.WebhookPayload, db: Session = Depends(get_db)):
    try:
        if payload.passphrase != WEBHOOK_PASSPHRASE:
            raise InvalidCredentialsError()

        user = crud.get_user(db, payload.username)
        if not user:
            raise UserNotFoundError(payload.username)
        
        try:
            client = create_client(user.api_key, user.api_secret, ENVIRONMENT)
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

            # Binance order parameters
            order_params = {
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": quantity,
                "reduceOnly": reduce_only  # Binance API uses camelCase
            }

            # Add price for limit orders
            if order_type == 'LIMIT':
                order_params["price"] = float(price)
                order_params["timeInForce"] = 'GTC'

            # Execute the order
            order = client.futures_create_order(**order_params)
            
            # Get the executed price
            executed_price = float(order.get("avgPrice", 0)) or float(order.get("price", 0))
            
            # Database trade record
            db_trade = Trade(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=executed_price,
                type=order_type,
                reduce_only=reduce_only,
                leverage=payload.leverage,
                timestamp=datetime.utcnow()
            )
            
            # Save trade to database
            db.add(db_trade)
            db.commit()
            
            return {
                "status": "success",
                "order": order,
                "trade_id": db_trade.id
            }
            
        except Exception as e:
            db.rollback()  # Rollback in case of error
            raise BinanceAPIError(str(e))
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Unexpected error in webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
