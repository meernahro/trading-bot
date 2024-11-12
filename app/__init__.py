# app/__init__.py

from fastapi import FastAPI
from .routes import trading_router, accounts_router, users_router, trades_router
from .database import Base, engine

# Create the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Trading API",
    description="API for managing trading accounts and executing trades",
    version="1.0.1"
)

# Include routers
app.include_router(users_router)
app.include_router(accounts_router)
app.include_router(trading_router)
app.include_router(trades_router)
