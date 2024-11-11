# app/routes/trades.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import SessionLocal
from ..utils.customLogger import get_logger
from ..models import Balance
from .. import models

logging = get_logger(name="trades")

router = APIRouter()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/trades/{username}", tags=["trades"], summary="Get all trades", response_model=schemas.TradesResponseModel)
async def get_trade_history(username: str, db: Session = Depends(get_db)):
    try:
        user = crud.get_user(db, username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        trades = crud.get_trades(db, user.id)
        trades_list = []
        for trade in trades:
            trade_dict = {
                "id": trade.id,
                "symbol": trade.symbol,
                "side": trade.side,
                "type": trade.type,
                "quantity": trade.quantity,
                "price": trade.price,
                "leverage": trade.leverage,
                "reduceOnly": str(trade.reduce_only),
                "timeInForce": "GTC",
                "status": "FILLED",
                "timestamp": trade.timestamp
            }
            trades_list.append(trade_dict)
        return {"status": "success", "trades": trades_list}
    except Exception as e:
        logging.error(f"Error fetching trade history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test/db", tags=["test"], summary="Get all database records")
async def get_all_db_records(db: Session = Depends(get_db)):
    try:
        # Get all users first
        users = db.query(models.User).all()
        users_list = [{
            'id': user.id,
            'username': user.username,
            'exchange': user.exchange,
            'market_type': user.market_type,
            'timestamp': user.timestamp
        } for user in users]
        
        # Get all trades for all users
        all_trades = []
        for user in users:
            trades = crud.get_trades(db, user.id)
            trades_list = [{k: v for k, v in trade.__dict__.items() if not k.startswith('_')} for trade in trades]
            all_trades.extend(trades_list)
        
        # Get all balances
        balances = db.query(models.Balance).order_by(models.Balance.timestamp.desc()).all()
        balances_list = [{k: v for k, v in balance.__dict__.items() if not k.startswith('_')} for balance in balances]
        
        # Get all positions
        positions = db.query(models.Position).order_by(models.Position.timestamp.desc()).all()
        positions_list = [{k: v for k, v in position.__dict__.items() if not k.startswith('_')} for position in positions]
        
        return {
            "status": "success",
            "data": {
                "users": users_list,
                "trades": all_trades,
                "balances": balances_list,
                "positions": positions_list
            }
        }
    except Exception as e:
        logging.error(f"Error fetching database records: {e}")
        raise HTTPException(status_code=500, detail=str(e))

