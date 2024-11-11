# app/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from .database import Base
from datetime import datetime

class Trade(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String)
    side = Column(String)
    quantity = Column(Float)
    price = Column(Float)
    type = Column(String)
    reduce_only = Column(Boolean, name='reduce_only')
    leverage = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Trade {self.symbol} {self.side} {self.quantity}>"

class Balance(Base):
    __tablename__ = 'balances'
    id = Column(Integer, primary_key=True, autoincrement=True)
    asset = Column(String)
    balance = Column(Float)
    available_balance = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Position(Base):
    __tablename__ = 'positions'
    id = Column(Integer, primary_key=True, autoincrement=True)
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

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True)
    exchange = Column(String)  # 'binance', etc.
    market_type = Column(String)  # 'spot' or 'futures'
    api_key = Column(String)
    api_secret = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
