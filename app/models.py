# app/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
import enum

class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"

class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    FAILED_VERIFICATION = "failed_verification"

class ExchangeType(str, enum.Enum):
    BINANCE = "binance"
    MEXC = "mexc"

class MarketType(str, enum.Enum):
    SPOT = "spot"
    FUTURES = "futures"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=True)
    status = Column(String, default=UserStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    trading_accounts = relationship("TradingAccount", back_populates="user", cascade="all, delete-orphan")

class TradingAccount(Base):
    __tablename__ = 'trading_accounts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    exchange = Column(String, nullable=False)
    market_type = Column(String, nullable=False)
    api_key = Column(String, nullable=False)
    api_secret = Column(String, nullable=False)
    status = Column(String, default=AccountStatus.PENDING_VERIFICATION)
    is_testnet = Column(Boolean, default=True)
    last_verified = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="trading_accounts")
    trades = relationship("Trade", back_populates="trading_account", cascade="all, delete-orphan")
    balances = relationship("Balance", back_populates="trading_account", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="trading_account", cascade="all, delete-orphan")

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trading_account_id = Column(Integer, ForeignKey('trading_accounts.id'), nullable=False)
    symbol = Column(String)
    side = Column(String)
    quantity = Column(Float)
    price = Column(Float)
    type = Column(String)
    reduce_only = Column(Boolean)
    leverage = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    trading_account = relationship("TradingAccount", back_populates="trades")

class Balance(Base):
    __tablename__ = 'balances'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trading_account_id = Column(Integer, ForeignKey('trading_accounts.id'), nullable=False)
    asset = Column(String)
    free = Column(Float)
    locked = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    trading_account = relationship("TradingAccount", back_populates="balances")

class Position(Base):
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trading_account_id = Column(Integer, ForeignKey('trading_accounts.id'), nullable=False)
    symbol = Column(String)
    positionSide = Column(String)
    positionAmt = Column(Float)
    entryPrice = Column(Float)
    breakEvenPrice = Column(Float)
    markPrice = Column(Float)
    unRealizedProfit = Column(Float)
    liquidationPrice = Column(Float)
    notional = Column(Float)
    marginAsset = Column(String)
    initialMargin = Column(Float)
    maintMargin = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    trading_account = relationship("TradingAccount", back_populates="positions")
