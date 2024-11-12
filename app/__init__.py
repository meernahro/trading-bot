# app/__init__.py

from fastapi import FastAPI
from .routes import trading_router, accounts_router, users_router, trades_router
from .database import Base, engine

# Create the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Trading Bot API",
    description="""
    A comprehensive API for managing cryptocurrency trading accounts and automated trading operations.
    
    ## Features
    * User Management
    * Trading Account Management
    * Automated Trading via Webhooks
    * Position Tracking
    * Balance Monitoring
    * Trade History
    
    ## Authentication
    All endpoints require proper authentication using API keys and secrets.
    
    ## Rate Limiting
    Please note that some endpoints may have rate limiting applied.
    """,
    version="1.0.1",
    contact={
        "name": "Trading Bot Support",
        "email": "support@tradingbot.com",
    },
    license_info={
        "name": "Private License",
        "url": "https://yourcompany.com/license",
    }
)

# Include routers
app.include_router(users_router)
app.include_router(accounts_router)
app.include_router(trading_router)
app.include_router(trades_router)
