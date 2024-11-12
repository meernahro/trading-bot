from fastapi import Request
from fastapi.responses import JSONResponse
from .utils.exceptions import BaseCustomException
from .utils.customLogger import get_logger
from typing import Callable
import traceback

logger = get_logger(name="middleware")

async def error_handler_middleware(request: Request, call_next: Callable):
    try:
        return await call_next(request)
    except BaseCustomException as e:
        # Handle our custom exceptions
        logger.error(f"Custom error occurred: {str(e)}")
        return JSONResponse(
            status_code=e.status_code,
            content={"status": "error", "detail": e.detail}
        )
    except Exception as e:
        # Handle unexpected exceptions
        logger.error(f"Unexpected error occurred: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "detail": "An unexpected error occurred"
            }
        ) 