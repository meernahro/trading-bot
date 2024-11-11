# app/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True)
    exchange = Column(String)  # 'binance', etc.
    market_type = Column(String)  # 'spot' or 'futures'
    api_key = Column(String)
    api_secret = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    trades = relationship("Trade", back_populates="user")
    balances = relationship("Balance", back_populates="user")
    positions = relationship("Position", back_populates="user")

class Trade(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    symbol = Column(String)
    side = Column(String)
    quantity = Column(Float)
    price = Column(Float)
    type = Column(String)
    reduce_only = Column(Boolean, name='reduce_only')
    leverage = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="trades")

class Balance(Base):
    __tablename__ = 'balances'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    asset = Column(String)
    balance = Column(Float)
    available_balance = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="balances")

class Position(Base):
    __tablename__ = 'positions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
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
    user = relationship("User", back_populates="positions")
