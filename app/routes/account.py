# app/routes/account.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..binanceClient import client
from ..database import SessionLocal
from ..utils.customLogger import get_logger

logging = get_logger(name="account")
router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/account/balance", tags=["account"], summary="Get USDT balance", response_model=schemas.BalanceResponseModel)
async def get_usdt_balance(db: Session = Depends(get_db)):
    try:
        account_info = client.futures_account_balance()
        usdt_balance = next((asset for asset in account_info if asset["asset"] == "USDT"), None)
        
        if not usdt_balance:
            return {"status": "error", "message": "USDT balance not found"}

        # Save balance to database
        crud.create_balance(db, usdt_balance)

        return {"status": "success", "balance": usdt_balance}
    except Exception as e:
        logging.error(f"Error fetching USDT balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/account/positions", tags=["account"], summary="Get open positions", response_model=schemas.PositionsResponseModel)
async def get_open_positions(db: Session = Depends(get_db)):
    try:
        positions = client.futures_position_information()
        open_positions = [pos for pos in positions if float(pos['positionAmt']) != 0]
        
        # Save positions to database
        crud.save_positions(db, open_positions)
        
        return {"status": "success", "open_positions": open_positions}
    except Exception as e:
        logging.error(f"Error fetching open positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/account/position/{symbol}", tags=["account"], summary="Get position information for a symbol", response_model=schemas.PositionInfoResponseModel)
async def get_position_info(symbol: str):
    try:
        positions = client.futures_position_information(symbol=symbol.upper())
        return {"status": "success", "position_info": positions}
    except Exception as e:
        logging.error(f"Error fetching position info for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
