# app/crud.py

from sqlalchemy.orm import Session
from . import models
from datetime import datetime
from .utils.exceptions import DatabaseError

def create_trade(db: Session, trade_data: dict, user_id: int):
    trade_data['user_id'] = user_id
    trade = models.Trade(**trade_data)
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade

def get_trades(db: Session, user_id: int):
    return db.query(models.Trade)\
        .filter(models.Trade.user_id == user_id)\
        .order_by(models.Trade.timestamp.desc())\
        .all()

def create_balance(db: Session, balance_data: dict, user_id: int):
    # Check if balance exists for this asset and user
    existing_balance = db.query(models.Balance).filter(
        models.Balance.asset == balance_data["asset"],
        models.Balance.user_id == user_id
    ).first()
    
    if existing_balance:
        existing_balance.balance = float(balance_data["balance"])
        existing_balance.available_balance = float(balance_data["availableBalance"])
        existing_balance.timestamp = datetime.utcnow()
        db.commit()
        return existing_balance
    else:
        balance = models.Balance(
            user_id=user_id,
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

def save_positions(db: Session, positions_data: list, user_id: int):
    # Delete existing positions for this user
    db.query(models.Position)\
        .filter(models.Position.user_id == user_id)\
        .delete()
    
    # Insert new positions
    for position in positions_data:
        position_model = models.Position(
            user_id=user_id,
            symbol=position["symbol"],
            positionSide=position["positionSide"],
            positionAmt=float(position["positionAmt"]),
            entryPrice=float(position["entryPrice"]),
            breakEvenPrice=float(position["breakEvenPrice"]),
            markPrice=float(position["markPrice"]),
            unRealizedProfit=float(position["unRealizedProfit"]),
            liquidationPrice=float(position["liquidationPrice"]),
            notional=float(position["notional"]),
            marginAsset=position["marginAsset"],
            initialMargin=float(position["initialMargin"]),
            maintMargin=float(position["maintMargin"]),
            timestamp=datetime.utcnow()
        )
        db.add(position_model)
    
    db.commit()

def get_positions(db: Session):
    return db.query(models.Position).all()

def create_user(db: Session, user_data: dict):
    user = models.User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user(db: Session, username: str):
    try:
        return db.query(models.User).filter(models.User.username == username).first()
    except Exception as e:
        raise DatabaseError(str(e))

def get_users(db: Session):
    return db.query(models.User).all()
