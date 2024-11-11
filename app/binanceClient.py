# app/binanceClient.py

import logging
from binance.client import Client
from .utils.customLogger import get_logger

logging = get_logger(name="binance_client")

def create_client(api_key: str, api_secret: str, environment: str = 'development'):
    client = Client(api_key, api_secret)
    
    if environment.lower() == 'development':
        logging.info("Running in development mode - using testnet")
        client.API_URL = 'https://testnet.binance.vision/api'
        client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'
    else:
        logging.info("Running in production mode - using live API")
        client.API_URL = 'https://api.binance.com/api'
        client.FUTURES_URL = 'https://fapi.binance.com/fapi'
    
    return client
