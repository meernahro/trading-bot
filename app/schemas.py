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
    KUCOIN = "kucoin"
    OKX = "okx"
    BYBIT = "bybit"

class MarketType(str, Enum):
    SPOT = "spot"
    FUTURES = "futures"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_MARKET = "STOP_MARKET"
    STOP_LIMIT = "STOP_LIMIT"
    MARKET_STOP = "MARKET_STOP"
    POST_ONLY = "POST_ONLY"
    IOC = "IOC"
    FOK = "FOK"

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, Enum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class PositionSide(str, Enum):
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
    passphrase: Optional[str] = None

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

# Base Order Schema
class OrderBase(BaseModel):
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: Optional[str] = "GTC"
    
# Order Request Schemas
class CreateOrderRequest(OrderBase):
    leverage: Optional[int] = Field(None, ge=1, le=125)

class OrderResponse(BaseModel):
    exchange: ExchangeType
    market_type: MarketType
    order_id: str
    status: OrderStatus
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: float
    executed_qty: float
    executed_price: Optional[float]
    commission: Optional[float]
    commission_asset: Optional[str]
    created_at: datetime

# Add these new schemas to the existing ones

class OrderBookEntry(BaseModel):
    price: float
    quantity: float

class OrderBook(BaseModel):
    symbol: str
    bids: List[List[float]]
    asks: List[List[float]]
    timestamp: int

class Trade(BaseModel):
    id: int
    price: float
    quantity: float
    timestamp: int
    maker: bool
    best_match: bool

class Kline(BaseModel):
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int
    quote_volume: float
    trades: int
    taker_buy_base: float
    taker_buy_quote: float

class Ticker24h(BaseModel):
    symbol: str
    price_change: float
    price_change_percent: float
    weighted_avg_price: float
    prev_close_price: float
    last_price: float
    last_qty: float
    bid_price: float
    ask_price: float
    open_price: float
    high_price: float
    low_price: float
    volume: float
    quote_volume: float
    open_time: int
    close_time: int
    count: int

class SymbolInfo(BaseModel):
    symbol: str
    status: str
    base_asset: str
    quote_asset: str
    min_price: float
    max_price: float
    tick_size: float
    min_qty: float
    max_qty: float
    step_size: float
    min_notional: float

class ExchangeInfo(BaseModel):
    timezone: str
    server_time: int
    rate_limits: List[Dict]
    symbols: List[SymbolInfo]
