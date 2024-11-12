from fastapi import HTTPException
from typing import Optional, Any

class BaseCustomException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)
        self.log_error()

    def log_error(self):
        """Log the error - can be overridden by subclasses"""
        pass

class DatabaseError(BaseCustomException):
    def __init__(self, detail: str):
        super().__init__(status_code=500, detail=f"Database error: {detail}")

class UserNotFoundError(BaseCustomException):
    def __init__(self, username: str):
        super().__init__(status_code=404, detail=f"User not found: {username}")

class InvalidCredentialsError(BaseCustomException):
    def __init__(self):
        super().__init__(status_code=403, detail="Invalid credentials")

class BinanceAPIError(BaseCustomException):
    def __init__(self, detail: str):
        super().__init__(status_code=502, detail=f"Binance API error: {detail}")

class ValidationError(BaseCustomException):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=f"Validation error: {detail}")

class AuthenticationError(BaseCustomException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=401, detail=detail)

class ForbiddenError(BaseCustomException):
    def __init__(self, detail: str = "Access forbidden"):
        super().__init__(status_code=403, detail=detail)

class ResourceNotFoundError(BaseCustomException):
    def __init__(self, resource_type: str, resource_id: Any):
        super().__init__(
            status_code=404, 
            detail=f"{resource_type} not found: {resource_id}"
        ) 