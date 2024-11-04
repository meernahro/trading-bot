# app/routes/trading.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..utils import client, logging
from ..database import SessionLocal
from ..config import WEBHOOK_PASSPHRASE

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
    if payload.passphrase != WEBHOOK_PASSPHRASE:
        logging.warning("Unauthorized access attempt with incorrect passphrase.")
        raise HTTPException(status_code=403, detail="Invalid passphrase")

    action = payload.action.lower()
    symbol = payload.symbol.upper()
    quantity = payload.quantity
    price = payload.price
    order_type = 'LIMIT' if price != "market" else 'MARKET'
    limit_price = float(price) if order_type == 'LIMIT' else None

    logging.info(f"Received webhook: action={action}, symbol={symbol}, quantity={quantity}, price={price}, leverage={payload.leverage}")

    try:
        client.futures_change_leverage(symbol=symbol, leverage=payload.leverage)
        
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
            logging.error(f"Invalid action received: {action}")
            raise HTTPException(status_code=400, detail="Invalid action")

        order_params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity,
            'reduceOnly': 'true' if reduce_only else 'false'
        }

        if order_type == 'LIMIT':
            order_params['price'] = limit_price
            order_params['timeInForce'] = 'GTC'

        logging.info(f"Order params: {order_params}")
        order = client.futures_create_order(**order_params)

        logging.info(f"Order executed: {order}")

        # Prepare trade data for the database
        trade_data = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity,
            'price': limit_price or 0.0,
            'leverage': payload.leverage,
            'reduceOnly': order_params.get('reduceOnly'),
            'timeInForce': order_params.get('timeInForce', ''),
            'status': 'EXECUTED'
        }

        # Save the trade to the database
        crud.create_trade(db, trade_data)

        return {"status": "success", "order": order}

    except Exception as e:
        logging.error(f"Error executing order: {e}")
        raise HTTPException(status_code=500, detail=str(e))
