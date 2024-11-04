# app/routes/trades.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import SessionLocal
from ..utils import logging

router = APIRouter()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/trades", tags=["trades"], summary="Get all trades", response_model=schemas.TradesResponseModel)
async def get_trade_history(db: Session = Depends(get_db)):
    try:
        trades = crud.get_trades(db)
        trades_list = [{k: v for k, v in trade.__dict__.items() if not k.startswith('_')} for trade in trades]
        return {"status": "success", "trades": trades_list}
    except Exception as e:
        logging.error(f"Error fetching trade history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
