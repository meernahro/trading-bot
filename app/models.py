# app/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime
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