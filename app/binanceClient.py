# app/binanceClient.py

import logging
from binance.client import Client
from .config import API_KEY, API_SECRET

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Initialize Binance client
client = Client(API_KEY, API_SECRET, testnet=True)
client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'  # For testnet
