# app/routes/account.py

from fastapi import APIRouter, HTTPException, Depends, status, Query, Path
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
from typing import List

logger = get_logger(name="account")
router = APIRouter(
    prefix="/account",
    tags=["account"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing credentials"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - Requested resource does not exist"},
        500: {"description": "Internal Server Error"},
        502: {"description": "Bad Gateway - Error communicating with Binance API"}
    }
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get(
    "/balance/{username}",
    summary="Get USDT Balance",
    response_model=schemas.BalanceResponseModel
)
async def get_usdt_balance(username: str, db: Session = Depends(get_db)):
    """
    ## Get USDT Balance
    
    Retrieves the USDT balance for a specific user.

    ### Parameters
    - `username` (str): Username of the account owner.
    
    ### Returns
    - **200 OK:** USDT balance details.
    
    ### Raises
    - **404 Not Found:** If the user or USDT balance does not exist.
    - **502 Bad Gateway:** If there's an error with the Binance API.
    - **500 Internal Server Error:** For unexpected errors.
    """
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

            crud.save_balances(db, [usdt_balance], user.id)
            return {"status": "success", "balance": usdt_balance}
            
        except BinanceAPIError as e:
            logger.error(f"Binance API error while fetching balance for user {username}: {e.detail}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error while fetching balance for user {username}: {e}")
            raise BinanceAPIError(str(e))
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Internal server error in get_usdt_balance for user {username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get(
    "/positions/{username}",
    summary="Get Open Positions",
    response_model=schemas.PositionsResponseModel
)
async def get_open_positions(username: str, db: Session = Depends(get_db)):
    """
    ## Get Open Positions
    
    Retrieves all open positions for a specific user.

    ### Parameters
    - `username` (str): Username of the account owner.
    
    ### Returns
    - **200 OK:** List of open positions.
    
    ### Raises
    - **404 Not Found:** If the user does not exist.
    - **502 Bad Gateway:** If there's an error with the Binance API.
    - **500 Internal Server Error:** For unexpected errors.
    """
    try:
        user = crud.get_user(db, username)
        if not user:
            raise UserNotFoundError(username)
        
        try:
            client = create_client(user.api_key, user.api_secret, ENVIRONMENT)
            positions = client.futures_position_information()
            open_positions = [pos for pos in positions if float(pos['positionAmt']) != 0]
            
            # Pass user_id to save_positions
            crud.save_positions(db, open_positions, user.id)
            
            return {"status": "success", "open_positions": open_positions}
        except BinanceAPIError as e:
            logger.error(f"Binance API error while fetching positions for user {username}: {e.detail}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error while fetching positions for user {username}: {e}")
            raise BinanceAPIError(str(e))
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Internal server error in get_open_positions for user {username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get(
    "/position/{symbol}",
    summary="Get Position Information for a Symbol",
    response_model=schemas.PositionInfoResponseModel
)
async def get_position_info(
    symbol: str = Path(..., description="Symbol of the position"),
    username: str = Query(..., description="Username of the account owner"),
    db: Session = Depends(get_db)
):
    """
    ## Get Position Information for a Symbol
    
    Retrieves position details for a specific symbol under a user's account.

    ### Parameters
    - `symbol` (str): Symbol of the position.
    - `username` (str): Username of the account owner.
    
    ### Returns
    - **200 OK:** Position information for the specified symbol.
    
    ### Raises
    - **404 Not Found:** If the user does not exist.
    - **502 Bad Gateway:** If there's an error with the Binance API.
    - **500 Internal Server Error:** For unexpected errors.
    """
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
            
        except BinanceAPIError as e:
            logger.error(f"Binance API error while fetching position info for {symbol}: {e.detail}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error while fetching position info for {symbol}: {e}")
            raise BinanceAPIError(str(e))
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Internal server error in get_position_info for {symbol}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
