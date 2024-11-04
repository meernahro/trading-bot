# app/config.py

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
WEBHOOK_PASSPHRASE = os.getenv('WEBHOOK_PASSPHRASE')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./trading_bot.db')
