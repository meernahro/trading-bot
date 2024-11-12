from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Dict, Tuple
import time
from ..utils.customLogger import get_logger

logger = get_logger(name="rate_limit")

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = {}
        
    def is_allowed(self, ip: str) -> Tuple[bool, float]:
        current_time = time.time()
        
        # Initialize or clean old requests
        if ip not in self.requests:
            self.requests[ip] = []
        self.requests[ip] = [req_time for req_time in self.requests[ip] 
                           if current_time - req_time < 60]
        
        # Check if rate limit is exceeded
        if len(self.requests[ip]) >= self.requests_per_minute:
            wait_time = 60 - (current_time - self.requests[ip][0])
            return False, wait_time
        
        # Add new request
        self.requests[ip].append(current_time)
        return True, 0

rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    is_allowed, wait_time = rate_limiter.is_allowed(client_ip)
    
    if not is_allowed:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        return JSONResponse(
            status_code=429,
            content={
                "status": "error",
                "detail": f"Rate limit exceeded. Please wait {int(wait_time)} seconds."
            }
        )
    
    return await call_next(request) 