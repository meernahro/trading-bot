# app/crud.py

from sqlalchemy.orm import Session
from datetime import datetime
from . import models, schemas
from typing import List, Optional
from .utils.exceptions import DatabaseError

# User CRUD operations
def get_user(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    try:
        db_user = models.User(
            username=user.username,
            email=user.email,
            status=models.UserStatus.ACTIVE
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Error creating user: {str(e)}")

def update_user(db: Session, username: str, user: schemas.UserUpdate) -> Optional[models.User]:
    try:
        db_user = get_user(db, username)
        if not db_user:
            return None
        
        update_data = user.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Error updating user: {str(e)}")

# Trading Account CRUD operations
def get_trading_account(db: Session, account_id: int) -> Optional[models.TradingAccount]:
    return db.query(models.TradingAccount).filter(models.TradingAccount.id == account_id).first()

def get_user_trading_accounts(db: Session, user_id: int) -> List[models.TradingAccount]:
    return db.query(models.TradingAccount).filter(models.TradingAccount.user_id == user_id).all()

def create_trading_account(db: Session, account: schemas.TradingAccountCreate, user_id: int) -> models.TradingAccount:
    try:
        db_account = models.TradingAccount(
            user_id=user_id,
            name=account.name,
            exchange=account.exchange,
            market_type=account.market_type,
            api_key=account.api_key,
            api_secret=account.api_secret,
            is_testnet=account.is_testnet,
            status=models.AccountStatus.PENDING_VERIFICATION
        )
        db.add(db_account)
        db.commit()
        db.refresh(db_account)
        return db_account
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Error creating trading account: {str(e)}")

def update_trading_account(
    db: Session, 
    account_id: int, 
    account: schemas.TradingAccountUpdate
) -> Optional[models.TradingAccount]:
    try:
        db_account = get_trading_account(db, account_id)
        if not db_account:
            return None

        update_data = account.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_account, field, value)
        
        db_account.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_account)
        return db_account
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Error updating trading account: {str(e)}")

def verify_trading_account(db: Session, account_id: int, verified: bool) -> Optional[models.TradingAccount]:
    try:
        db_account = get_trading_account(db, account_id)
        if not db_account:
            return None

        db_account.status = (
            models.AccountStatus.ACTIVE if verified 
            else models.AccountStatus.FAILED_VERIFICATION
        )
        db_account.last_verified = datetime.utcnow()
        db_account.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_account)
        return db_account
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Error verifying trading account: {str(e)}")

# Trade CRUD operations
def create_trade(db: Session, trade: schemas.TradeCreate) -> models.Trade:
    try:
        db_trade = models.Trade(**trade.dict())
        db.add(db_trade)
        db.commit()
        db.refresh(db_trade)
        return db_trade
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Error creating trade: {str(e)}")

def get_account_trades(
    db: Session, 
    account_id: int, 
    skip: int = 0, 
    limit: int = 100
) -> List[models.Trade]:
    return db.query(models.Trade)\
        .filter(models.Trade.trading_account_id == account_id)\
        .order_by(models.Trade.timestamp.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

# Position CRUD operations
def save_positions(db: Session, positions_data: list, account_id: int):
    try:
        # Delete existing positions for this account
        db.query(models.Position)\
            .filter(models.Position.trading_account_id == account_id)\
            .delete()
        
        # Insert new positions
        for position in positions_data:
            position_model = models.Position(
                trading_account_id=account_id,
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
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Error saving positions: {str(e)}")

# Balance CRUD operations
def save_balances(db: Session, balances_data: list, account_id: int):
    try:
        # Delete existing balances for this account
        db.query(models.Balance)\
            .filter(models.Balance.trading_account_id == account_id)\
            .delete()
        
        # Insert new balances
        for balance in balances_data:
            balance_model = models.Balance(
                trading_account_id=account_id,
                asset=balance["asset"],
                free=float(balance["free"]),
                locked=float(balance["locked"]),
                timestamp=datetime.utcnow()
            )
            db.add(balance_model)
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Error saving balances: {str(e)}")
