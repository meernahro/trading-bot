# app/__init__.py

from fastapi import FastAPI
from .routes import trading, account, trades, users
from .database import Base, engine

# Create the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Binance Futures Webhook", description="Webhook for Binance Futures", version="1.0.1")

# Include routers
app.include_router(trading.router)
app.include_router(account.router)
app.include_router(trades.router)
app.include_router(users.router)
