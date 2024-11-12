# app/routes/__init__.py

from .binance_futures import router as binance_futures_router
from .accounts import router as accounts_router
from .users import router as users_router
from .trades import router as trades_router

__all__ = [
    "binance_futures_router",
    "accounts_router",
    "users_router",
    "trades_router"
]
