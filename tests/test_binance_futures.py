import requests
import json
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://127.0.0.1:8080"
TEST_SYMBOL = "BTCUSDT"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpassword123"
TEST_EMAIL = "test@example.com"

def log_response(response, endpoint):
    print(f"\n{'='*50}")
    print(f"Testing: {endpoint}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print(f"{'='*50}\n")

def ensure_test_user():
    endpoint = "/users/"
    payload = {
        "username": TEST_USERNAME,
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    # Try to get user first
    response = requests.get(f"{BASE_URL}/users/{TEST_USERNAME}")
    if response.status_code == 200:
        print("Test user already exists")
        return True
        
    # Create user if doesn't exist
    response = requests.post(f"{BASE_URL}{endpoint}", json=payload)
    if response.status_code == 201:
        print("Created test user successfully")
        return True
    elif response.status_code == 400 and "already exists" in response.json().get("detail", ""):
        print("Test user already exists")
        return True
    else:
        print(f"Failed to ensure test user exists: {response.status_code}")
        print(response.json())
        return False

def create_trading_account():
    endpoint = "/accounts/"  # Changed from /account/ to /accounts/
    payload = {
        "name": "Binance Futures Test",
        "exchange": "binance",
        "market_type": "futures",
        "is_testnet": True,
        "api_key": "580a68dfb45d33cc1479baee1b1019386e94e9ed99c107382571234c093f43da",
        "api_secret": "906d3c4977049478febe8141e2b964bd61714fb53263f97c1109a8a02135a546"
    }
    params = {
        "username": TEST_USERNAME
    }
    response = requests.post(
        f"{BASE_URL}{endpoint}", 
        json=payload,
        params=params
    )
    log_response(response, endpoint)
    if response.status_code in [200, 201]:
        return response.json()["id"]
    return None

def verify_account(account_id):
    endpoint = f"/accounts/{account_id}/verify"
    params = {"verified": "true"}
    response = requests.post(
        f"{BASE_URL}{endpoint}", 
        params=params
    )
    log_response(response, endpoint)
    return response.status_code in [200, 201]

def test_get_account_info(account_id):
    endpoint = f"/binance/futures/account?account_id={account_id}"
    response = requests.get(f"{BASE_URL}{endpoint}")
    log_response(response, endpoint)
    return response.status_code == 200

def test_get_positions(account_id):
    endpoint = f"/binance/futures/positions?account_id={account_id}"
    response = requests.get(f"{BASE_URL}{endpoint}")
    log_response(response, endpoint)
    
    if response.status_code == 200:
        data = response.json()
        if data["status"] == "success":
            positions = data.get("positions", [])
            print(f"Found {len(positions)} positions")
            return True
        else:
            print(f"Failed to get positions: {data.get('detail', 'Unknown error')}")
            return False
    elif response.status_code == 502:
        error_msg = response.json().get("detail", "")
        if "no positions" in error_msg.lower():
            print("No active positions found (this is normal for a new account)")
            return True
        print(f"Failed to get positions: {error_msg}")
        return False
    else:
        print(f"Unexpected status code: {response.status_code}")
        return False

def test_open_position(account_id):
    # First set leverage
    leverage_endpoint = f"/binance/futures/leverage"
    leverage_payload = {
        "symbol": TEST_SYMBOL,
        "leverage": 10
    }
    leverage_params = {"account_id": account_id}
    
    response = requests.post(
        f"{BASE_URL}{leverage_endpoint}", 
        json=leverage_payload,
        params=leverage_params
    )
    log_response(response, "Setting Leverage")
    if response.status_code != 200:
        print("Failed to set leverage")
        return False
        
    # Get current price
    price_response = requests.get(f"{BASE_URL}/binance/futures/price?symbol={TEST_SYMBOL}&account_id={account_id}")
    if price_response.status_code != 200:
        print("Failed to get current price")
        return False
    
    current_price = float(price_response.json()["price"])
    print(f"Current {TEST_SYMBOL} price: {current_price}")
    
    # Calculate quantity to ensure minimum notional of 100 USDT
    min_notional = 100  # Minimum notional value in USDT
    quantity = round(min_notional / current_price + 0.001, 3)  # Add small buffer and round to 3 decimals
    notional_value = quantity * current_price
    
    print(f"Calculated quantity: {quantity} {TEST_SYMBOL}")
    print(f"Notional value: {notional_value} USDT")
    
    # Then open position
    endpoint = f"/binance/futures/position/open?account_id={account_id}"
    payload = {
        "symbol": TEST_SYMBOL,
        "side": "LONG",
        "type": "MARKET",
        "quantity": quantity,
        "leverage": 10
    }
    
    print(f"Sending order payload: {payload}")
    response = requests.post(f"{BASE_URL}{endpoint}", json=payload)
    log_response(response, "Opening Position")
    
    if response.status_code != 200:
        print(f"Failed to open position: {response.json().get('detail', 'Unknown error')}")
        return False
        
    return True

def test_close_position(account_id):
    # Get current position size
    positions_response = requests.get(f"{BASE_URL}/binance/futures/positions?account_id={account_id}&symbol={TEST_SYMBOL}")
    if positions_response.status_code != 200:
        print("Failed to get current position")
        return False
        
    positions = positions_response.json().get("positions", [])
    btc_positions = [p for p in positions if p["symbol"] == TEST_SYMBOL]
    
    if not btc_positions:
        print("No BTC position to close")
        return False
        
    position = btc_positions[0]
    quantity = abs(float(position["positionAmt"]))
    
    print(f"Closing position of {quantity} {TEST_SYMBOL}")
    
    endpoint = f"/binance/futures/position/close?account_id={account_id}"
    payload = {
        "symbol": TEST_SYMBOL,
        "side": "LONG" if float(position["positionAmt"]) > 0 else "SHORT",
        "type": "MARKET",
        "quantity": quantity,
        "reduce_only": True  # Add this to ensure we're only closing positions
    }
    
    print(f"Sending close order payload: {payload}")
    response = requests.post(f"{BASE_URL}{endpoint}", json=payload)
    log_response(response, "Closing Position")
    
    if response.status_code != 200:
        print(f"Failed to close position: {response.json().get('detail', 'Unknown error')}")
        return False
        
    return True

def main():
    print("Starting Binance Futures API Tests...")
    print(f"Test Time: {datetime.now()}")
    
    # Step 1: Ensure test user exists
    print("\nStep 1: Ensuring test user exists...")
    if not ensure_test_user():
        print("Failed to ensure test user exists")
        return
    
    # Step 2: Create Trading Account
    print("\nStep 2: Creating Trading Account...")
    account_id = create_trading_account()
    if not account_id:
        print("Failed to create trading account")
        return
    
    # Step 3: Verify Account
    print("\nStep 3: Verifying Trading Account...")
    if not verify_account(account_id):
        print("Failed to verify account")
        return
    
    # Step 4: Get Account Info
    print("\nStep 4: Getting Account Info...")
    if not test_get_account_info(account_id):
        print("Failed to get account info")
        return
    
    # Step 5: Get Positions
    print("\nStep 5: Getting Positions...")
    if not test_get_positions(account_id):
        print("Failed to get positions")
        return
    
    # Step 6: Open Position
    print("\nStep 6: Opening Position...")
    if not test_open_position(account_id):
        print("Failed to open position")
        return
    
    # Wait for position to be opened
    print("\nWaiting for position to be processed...")
    time.sleep(2)
    
    # Step 7: Close Position
    print("\nStep 7: Closing Position...")
    if not test_close_position(account_id):
        print("Failed to close position")
        return
    
    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    main()