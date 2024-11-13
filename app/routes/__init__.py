# app/routes/__init__.py

from .binance_spot import router as binance_spot_router
from .mexc_spot import router as mexc_spot_router
from .accounts import router as accounts_router
from .users import router as users_router
from .trades import router as trades_router

__all__ = [
    "binance_spot_router",
    "mexc_spot_router",
    "accounts_router",
    "users_router",
    "trades_router"
]
