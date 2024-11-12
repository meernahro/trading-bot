# app/__init__.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import binance_futures_router, accounts_router, users_router, trades_router
from .database import Base, engine
from .middleware import error_handler_middleware
from .config import ALLOWED_HOSTS

# Create the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Trading Bot API",
    description="""
    A comprehensive API for managing cryptocurrency trading operations.
    
    ## Features
    * User Management
    * Trading Account Management
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add error handler middleware
app.middleware("http")(error_handler_middleware)

# Include routers
app.include_router(users_router)
app.include_router(accounts_router)
app.include_router(binance_futures_router)
app.include_router(trades_router)
