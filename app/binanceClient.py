# app/binanceClient.py

import logging
from binance.client import Client
from .config import API_KEY, API_SECRET, ENVIRONMENT
from .utils.customLogger import get_logger

logging = get_logger(name="binance_client")

# Initialize Binance client based on environment
client = Client(API_KEY, API_SECRET)

if ENVIRONMENT.lower() == 'development':
    logging.info("Running in development mode - using testnet")
    client.API_URL = 'https://testnet.binance.vision/api'
    client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'
else:
    logging.info("Running in production mode - using live API")
    # Use default URLs for production environment
    client.API_URL = 'https://api.binance.com/api'
    client.FUTURES_URL = 'https://fapi.binance.com/fapi'
