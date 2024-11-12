@echo off
:: Create and activate virtual environment
python -m venv venv
call venv\Scripts\activate

:: Install dependencies
pip install requests

:: Run the test script
python tests/test_binance_futures.py
pause