from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from binance.client import Client
from dotenv import load_dotenv
import os
import logging
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.types import Boolean

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Initialize FastAPI app
app = FastAPI(title="Binance Futures Webhook", description="Webhook for Binance Futures", version="1.0.1")

# Retrieve API keys and passphrase from environment variables
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
WEBHOOK_PASSPHRASE = os.getenv('WEBHOOK_PASSPHRASE')

# Initialize Binance client
client = Client(API_KEY, API_SECRET, testnet=True)
client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'  # For testnet

#  Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///trading_bot.db')
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Define a Trade Model
class Trade(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String)
    side = Column(String)
    type = Column(String)
    quantity = Column(Float)
    price = Column(Float)
    leverage = Column(Integer)
    reduceOnly = Column(String)
    timeInForce = Column(String)
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.now)

# Create the database tables
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define the payload schema
class WebhookPayload(BaseModel):
    passphrase: str
    action: str
    symbol: str
    quantity: float
    price: str
    leverage: int = 1

# Define the webhook endpoint
@app.post("/webhook", tags=["trading"], summary="Execute a trading action")
async def webhook(payload: WebhookPayload):
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

        # Save the trade to the database
        db = SessionLocal()
        trade = Trade(**order_params, status='EXECUTED', leverage=payload.leverage)
        db.add(trade)
        db.commit()
        db.refresh(trade)
        db.close()


        return {"status": "success", "order": order}

    except Exception as e:
        logging.error(f"Error executing order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get USDT balance
@app.get("/account/balance", tags=["account"], summary="Get USDT balance")
async def get_usdt_balance():
    try:
        account_info = client.futures_account_balance()
        usdt_balance = next((asset for asset in account_info if asset["asset"] == "USDT"), None)
        
        if not usdt_balance:
            return {"status": "error", "message": "USDT balance not found"}

        return {"status": "success", "balance": usdt_balance}
    except Exception as e:
        logging.error(f"Error fetching USDT balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to fetch open positions
@app.get("/account/positions", tags=["account"], summary="Get open positions")
async def get_open_positions():
    try:
        positions = client.futures_position_information()
        open_positions = [pos for pos in positions if float(pos['positionAmt']) != 0]
        return {"status": "success", "open_positions": open_positions}
    except Exception as e:
        logging.error(f"Error fetching open positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to fetch position information by symbol
@app.get("/account/position/{symbol}", tags=["account"], summary="Get position information for a symbol")
async def get_position_info(symbol: str):
    try:
        positions = client.futures_position_information(symbol=symbol.upper())
        return {"status": "success", "position_info": positions}
    except Exception as e:
        logging.error(f"Error fetching position info for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to fetch all trades
@app.get("/trades", tags=["trades"], summary="Get all trades")
async def get_trade_history():
    try:
        db = SessionLocal()
        trades = db.query(Trade).order_by(Trade.timestamp.desc()).all()
        db.close()
        return {"status": "success", "trades": trades}
    except Exception as e:
        logging.error(f"Error fetching trade history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
