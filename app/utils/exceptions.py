from fastapi import HTTPException

class DatabaseError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=500, detail=f"Database error: {detail}")

class UserNotFoundError(HTTPException):
    def __init__(self, username: str):
        super().__init__(status_code=404, detail=f"User not found: {username}")

class InvalidCredentialsError(HTTPException):
    def __init__(self):
        super().__init__(status_code=403, detail="Invalid credentials")

class BinanceAPIError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=502, detail=f"Binance API error: {detail}") 