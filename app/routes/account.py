# app/routes/account.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..binanceClient import create_client
from ..database import SessionLocal
from ..utils.customLogger import get_logger
from ..config import ENVIRONMENT
from ..utils.exceptions import (
    DatabaseError,
    UserNotFoundError,
    InvalidCredentialsError,
    BinanceAPIError
)

logging = get_logger(name="account")
router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/account/balance/{username}", tags=["account"], summary="Get USDT balance", response_model=schemas.BalanceResponseModel)
async def get_usdt_balance(username: str, db: Session = Depends(get_db)):
    try:
        user = crud.get_user(db, username)
        if not user:
            raise UserNotFoundError(username)
        
        try:
            client = create_client(user.api_key, user.api_secret, ENVIRONMENT)
            account_info = client.futures_account_balance()
            usdt_balance = next((asset for asset in account_info if asset["asset"] == "USDT"), None)
            
            if not usdt_balance:
                raise HTTPException(status_code=404, detail="USDT balance not found")

            crud.create_balance(db, usdt_balance)
            return {"status": "success", "balance": usdt_balance}
            
        except Exception as e:
            raise BinanceAPIError(str(e))
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Unexpected error in get_usdt_balance: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/account/positions/{username}", tags=["account"], summary="Get open positions", response_model=schemas.PositionsResponseModel)
async def get_open_positions(username: str, db: Session = Depends(get_db)):
    try:
        user = crud.get_user(db, username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        client = create_client(user.api_key, user.api_secret, ENVIRONMENT)
        positions = client.futures_position_information()
        open_positions = [pos for pos in positions if float(pos['positionAmt']) != 0]
        
        # Save positions to database
        crud.save_positions(db, open_positions)
        
        return {"status": "success", "open_positions": open_positions}
    except Exception as e:
        logging.error(f"Error fetching open positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/account/position/{symbol}", tags=["account"], summary="Get position information for a symbol", response_model=schemas.PositionInfoResponseModel)
async def get_position_info(symbol: str, username: str, db: Session = Depends(get_db)):
    try:
        # Get user from database
        user = crud.get_user(db, username)
        if not user:
            raise UserNotFoundError(username)
        
        try:
            # Create Binance client
            client = create_client(user.api_key, user.api_secret, ENVIRONMENT)
            positions = client.futures_position_information(symbol=symbol.upper())
            return {"status": "success", "position_info": positions}
            
        except Exception as e:
            raise BinanceAPIError(str(e))
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Error fetching position info for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
