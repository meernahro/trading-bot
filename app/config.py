# app/config.py

import os
from dotenv import load_dotenv
from typing import List

# Load environment variables
load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./data/trading_bot.db')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')  # Default to development if not specified
ALLOWED_HOSTS: List[str] = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
