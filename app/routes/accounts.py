from fastapi import APIRouter, HTTPException, Depends, status, Query, Path, Body
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db
from ..utils.exceptions import DatabaseError
from ..utils.customLogger import get_logger
from typing import List

logger = get_logger(name="accounts")
router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
    responses={
        401: {"description": "Unauthorized"},
        500: {"description": "Internal Server Error"}
    }
)

@router.post("/", response_model=schemas.TradingAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_trading_account(
    account: schemas.TradingAccountCreate,
    username: str = Query(..., description="Username of the account owner"),
    db: Session = Depends(get_db)
):
    """
    Create a new trading account for a user.

    ## Description
    Creates a new trading account with specified exchange credentials and settings.

    ## Parameters
    * `account`: Trading account details including:
        * `name`: Account identifier
        * `exchange`: Exchange platform (binance/mexc)
        * `market_type`: Trading market (spot/futures)
        * `api_key`: Exchange API key
        * `api_secret`: Exchange API secret
        * `is_testnet`: Whether to use testnet (default: true)
    * `username`: Owner's username

    ## Returns
    Newly created trading account details

    ## Raises
    * `404`: User not found
    * `400`: Invalid account details
    * `500`: Database error
    """
    try:
        user = crud.get_user(db, username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {username} not found"
            )
        
        return crud.create_trading_account(db, account, user.id)
    except DatabaseError as e:
        logger.error(f"Database error while creating trading account: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while creating trading account: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/user/{username}", response_model=schemas.TradingAccountListResponse)
async def get_user_accounts(
    username: str = Path(..., description="Username to fetch accounts for"),
    db: Session = Depends(get_db)
):
    """
    Retrieve all trading accounts for a user.

    ## Description
    Lists all trading accounts associated with the specified user.

    ## Returns
    List of trading accounts with their current status and settings

    ## Raises
    * `404`: User not found
    * `500`: Server error
    """
    try:
        user = crud.get_user(db, username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {username} not found"
            )
        
        accounts = crud.get_user_trading_accounts(db, user.id)
        return {"status": "success", "accounts": accounts}
    except Exception as e:
        logger.error(f"Error fetching accounts for user {username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{account_id}", response_model=schemas.TradingAccountResponse)
async def get_trading_account(
    account_id: int = Path(..., description="Trading account ID to fetch"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific trading account.

    ## Description
    Gets detailed information about a specific trading account.

    ## Returns
    Trading account details including status and settings

    ## Raises
    * `404`: Account not found
    * `500`: Server error
    """
    try:
        account = crud.get_trading_account(db, account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trading account {account_id} not found"
            )
        return account
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trading account {account_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{account_id}", response_model=schemas.TradingAccountResponse)
async def update_trading_account(
    account_id: int = Path(..., description="Trading account ID to update"),
    account_update: schemas.TradingAccountUpdate = Body(..., description="Updated account details"),
    db: Session = Depends(get_db)
):
    """
    Update a trading account.

    ## Description
    Updates specified fields of a trading account.

    ## Parameters
    * `account_update`: Fields to update:
        * `name`: New account name
        * `api_key`: New API key
        * `api_secret`: New API secret
        * `status`: New account status
        * `is_testnet`: Update testnet setting

    ## Returns
    Updated trading account details

    ## Raises
    * `404`: Account not found
    * `400`: Invalid update data
    * `500`: Server error
    """
    try:
        updated_account = crud.update_trading_account(db, account_id, account_update)
        if not updated_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trading account {account_id} not found"
            )
        return updated_account
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating trading account {account_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{account_id}/verify", response_model=schemas.TradingAccountResponse)
async def verify_trading_account(
    account_id: int,
    verified: bool,
    db: Session = Depends(get_db)
):
    try:
        account = crud.verify_trading_account(db, account_id, verified)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trading account {account_id} not found"
            )
        return account
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying trading account {account_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) 