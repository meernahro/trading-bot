# app/crud.py

from sqlalchemy.orm import Session
from . import models
from datetime import datetime

def create_trade(db: Session, trade_data: dict):
    trade = models.Trade(**trade_data)
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade

def get_trades(db: Session):
    return db.query(models.Trade).order_by(models.Trade.timestamp.desc()).all()

def create_balance(db: Session, balance_data: dict):
    # Check if balance exists for this asset
    existing_balance = db.query(models.Balance).filter(
        models.Balance.asset == balance_data["asset"]
    ).first()
    
    if existing_balance:
        # Update existing balance
        existing_balance.balance = float(balance_data["balance"])
        existing_balance.available_balance = float(balance_data["availableBalance"])
        existing_balance.timestamp = datetime.utcnow()
        db.commit()
        return existing_balance
    else:
        # Create new balance if none exists
        balance = models.Balance(
            asset=balance_data["asset"],
            balance=float(balance_data["balance"]),
            available_balance=float(balance_data["availableBalance"]),
            timestamp=datetime.utcnow()
        )
        db.add(balance)
        db.commit()
        db.refresh(balance)
        return balance

def get_latest_balance(db: Session, asset: str):
    return db.query(models.Balance)\
        .filter(models.Balance.asset == asset)\
        .order_by(models.Balance.timestamp.desc())\
        .first()
