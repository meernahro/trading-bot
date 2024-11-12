# app/schemas.py

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import List, Optional, Dict, Union, Any
from enum import Enum
from decimal import Decimal

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

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class OrderSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"

# Base Response Models
class GenericResponse(BaseModel):
    status: str
    message: str

class ErrorDetail(BaseModel):
    loc: List[str]
    msg: str
    type: str

class HTTPError(BaseModel):
    detail: Union[str, List[ErrorDetail]]

class ErrorResponse(BaseModel):
    status: str = "error"
    detail: str

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
    api_key: str = Field(..., min_length=10)
    api_secret: str = Field(..., min_length=10)

class TradingAccountUpdate(BaseModel):
    name: Optional[str] = None
    api_key: Optional[str] = Field(None, min_length=10)
    api_secret: Optional[str] = Field(None, min_length=10)
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

# Trade Schemas
class TradeBase(BaseModel):
    symbol: str
    side: str
    quantity: float
    price: float
    type: OrderType
    reduce_only: bool = False
    leverage: Optional[int] = None

class TradeCreate(TradeBase):
    trading_account_id: int

class Trade(TradeBase):
    id: int
    timestamp: datetime
    trading_account_id: int
    order_id: Optional[str]
    commission: Optional[float]
    commission_asset: Optional[str]
    realized_pnl: Optional[float]

    class Config:
        from_attributes = True

# Position Schemas
class PositionBase(BaseModel):
    symbol: str
    positionSide: str
    positionAmt: float
    entryPrice: float
    markPrice: float
    unRealizedProfit: float
    liquidationPrice: float
    leverage: int
    marginType: str

class Position(PositionBase):
    id: int
    trading_account_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# Binance Futures Schemas
class OpenPositionRequest(BaseModel):
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float] = None  # Required for LIMIT orders
    leverage: int = Field(..., ge=1, le=125)

class ClosePositionRequest(BaseModel):
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float] = None

class OrderResponse(BaseModel):
    status: str
    order: Dict

class PositionsResponse(BaseModel):
    status: str
    positions: List[Dict[str, Any]]

    class Config:
        arbitrary_types_allowed = True

class FuturesAccountResponse(BaseModel):
    status: str
    account: Dict

# Response Models for Lists
class UserResponse(User):
    trading_accounts: List[TradingAccount] = []

class UserListResponse(BaseModel):
    status: str = "success"
    users: List[UserResponse]

class TradingAccountResponse(TradingAccount):
    pass

class TradingAccountListResponse(BaseModel):
    status: str = "success"
    accounts: List[TradingAccountResponse]

class TradeListResponse(BaseModel):
    status: str = "success"
    trades: List[Trade]

class PositionListResponse(BaseModel):
    status: str = "success"
    positions: List[Position]

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

class LeverageRequest(BaseModel):
    symbol: str
    leverage: int = Field(..., ge=1, le=125)

class LeverageResponse(BaseModel):
    status: str
    leverage: Dict

class PriceResponse(BaseModel):
    price: str
