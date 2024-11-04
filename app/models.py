# app/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from .database import Base
from datetime import datetime

class Trade(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String)
    side = Column(String)
    type = Column(String)
    quantity = Column(Float)
    price = Column(Float)
    leverage = Column(Integer)
    reduceOnly = Column(String)
    timeInForce = Column(String)
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

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
