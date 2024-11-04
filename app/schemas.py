# app/schemas.py

from pydantic import BaseModel
from typing import List
from datetime import datetime

# Request payload schema
class WebhookPayload(BaseModel):
    passphrase: str
    action: str
    symbol: str
    quantity: float
    price: str
    leverage: int = 1

# Response models
class OrderResponseModel(BaseModel):
    orderId: int
    symbol: str
    status: str
    clientOrderId: str
    price: str
    avgPrice: str
    origQty: str
    executedQty: str
    cumQty: str
    cumQuote: str
    timeInForce: str
    type: str
    reduceOnly: bool
    closePosition: bool
    side: str
    positionSide: str
    stopPrice: str
    workingType: str
    priceProtect: bool
    origType: str
    priceMatch: str
    selfTradePreventionMode: str
    goodTillDate: int
    updateTime: int

class WebhookResponseModel(BaseModel):
    status: str
    order: OrderResponseModel

class BalanceModel(BaseModel):
    accountAlias: str
    asset: str
    balance: str
    crossWalletBalance: str
    crossUnPnl: str
    availableBalance: str
    maxWithdrawAmount: str
    marginAvailable: bool
    updateTime: int

class BalanceResponseModel(BaseModel):
    status: str
    balance: BalanceModel

class PositionModel(BaseModel):
    symbol: str
    positionSide: str
    positionAmt: str
    entryPrice: str
    breakEvenPrice: str
    markPrice: str
    unRealizedProfit: str
    liquidationPrice: str
    isolatedMargin: str
    notional: str
    marginAsset: str
    isolatedWallet: str
    initialMargin: str
    maintMargin: str
    positionInitialMargin: str
    openOrderInitialMargin: str
    adl: int
    bidNotional: str
    askNotional: str
    updateTime: int

class PositionsResponseModel(BaseModel):
    status: str
    open_positions: List[PositionModel]

class PositionInfoResponseModel(BaseModel):
    status: str
    position_info: List[PositionModel]

class TradeModel(BaseModel):
    id: int
    symbol: str
    side: str
    type: str
    quantity: float
    price: float
    leverage: int
    reduceOnly: str
    timeInForce: str
    status: str
    timestamp: datetime

class TradesResponseModel(BaseModel):
    status: str
    trades: List[TradeModel]

class BalanceDBModel(BaseModel):
    id: int
    asset: str
    balance: float
    available_balance: float
    timestamp: datetime

    class Config:
        orm_mode = True
