# app/routes/__init__.py

from .trading import router as trading_router
from .account import router as account_router
from .trades import router as trades_router

__all__ = ["trading_router", "account_router", "trades_router"]
