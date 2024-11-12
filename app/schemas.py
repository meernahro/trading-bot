# app/schemas.py

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional
from enum import Enum

# Enums
class UserStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"

class AccountStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    FAILED_VERIFICATION = "failed_verification"

class ExchangeType(str, Enum):
    BINANCE = "binance"
    MEXC = "mexc"

class MarketType(str, Enum):
    SPOT = "spot"
    FUTURES = "futures"

# User Schemas
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    status: Optional[UserStatus] = None

class User(UserBase):
    id: int
    status: UserStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Trading Account Schemas
class TradingAccountBase(BaseModel):
    name: str
    exchange: ExchangeType
    market_type: MarketType
    is_testnet: bool = True

class TradingAccountCreate(TradingAccountBase):
    api_key: str
    api_secret: str

class TradingAccountUpdate(BaseModel):
    name: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    status: Optional[AccountStatus] = None
    is_testnet: Optional[bool] = None

class TradingAccount(TradingAccountBase):
    id: int
    user_id: int
    status: AccountStatus
    last_verified: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Response Models
class UserResponse(User):
    trading_accounts: List[TradingAccount] = []

class TradingAccountResponse(TradingAccount):
    pass

# Trade Schemas
class TradeBase(BaseModel):
    symbol: str
    side: str
    quantity: float
    price: float
    type: str
    reduce_only: bool
    leverage: int

class TradeCreate(TradeBase):
    trading_account_id: int

class Trade(TradeBase):
    id: int
    timestamp: datetime
    trading_account_id: int

    class Config:
        from_attributes = True

# Position Schemas
class PositionBase(BaseModel):
    symbol: str
    positionSide: str
    positionAmt: float
    entryPrice: float
    breakEvenPrice: float
    markPrice: float
    unRealizedProfit: float
    liquidationPrice: float
    notional: float
    marginAsset: str
    initialMargin: float
    maintMargin: float

class Position(PositionBase):
    id: int
    trading_account_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# Balance Schemas
class BalanceBase(BaseModel):
    asset: str
    free: float
    locked: float

class Balance(BalanceBase):
    id: int
    trading_account_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# Response Models for Lists
class UserListResponse(BaseModel):
    status: str = "success"
    users: List[UserResponse]

class TradingAccountListResponse(BaseModel):
    status: str = "success"
    accounts: List[TradingAccountResponse]

class TradeListResponse(BaseModel):
    status: str = "success"
    trades: List[Trade]

class PositionListResponse(BaseModel):
    status: str = "success"
    positions: List[Position]

class BalanceListResponse(BaseModel):
    status: str = "success"
    balances: List[Balance]

# Error Response Model
class ErrorResponse(BaseModel):
    status: str = "error"
    detail: str

# Webhook Schemas
class WebhookPayload(BaseModel):
    passphrase: str
    account_id: int
    action: str
    symbol: str
    leverage: int
    quantity: float
    price: str  # "market" or actual price

class WebhookResponseModel(BaseModel):
    status: str
    order: dict

# Trade Statistics Schema
class TradeStats(BaseModel):
    period: str
    total_trades: int
    total_volume: float
    win_rate: float
    start_date: Optional[datetime]
    end_date: datetime

class TradeStatsResponse(BaseModel):
    status: str = "success"
    stats: TradeStats
