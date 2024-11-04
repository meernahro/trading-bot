# app/routes/account.py

from fastapi import APIRouter, HTTPException
from .. import schemas
from ..utils import client, logging

router = APIRouter()

@router.get("/account/balance", tags=["account"], summary="Get USDT balance", response_model=schemas.BalanceResponseModel)
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

@router.get("/account/positions", tags=["account"], summary="Get open positions", response_model=schemas.PositionsResponseModel)
async def get_open_positions():
    try:
        positions = client.futures_position_information()
        open_positions = [pos for pos in positions if float(pos['positionAmt']) != 0]
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
