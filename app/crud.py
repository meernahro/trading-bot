# app/crud.py

from sqlalchemy.orm import Session
from . import models

def create_trade(db: Session, trade_data: dict):
    trade = models.Trade(**trade_data)
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade

def get_trades(db: Session):
    return db.query(models.Trade).order_by(models.Trade.timestamp.desc()).all()
