from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db
from ..utils.exceptions import DatabaseError
from ..utils.customLogger import get_logger
from typing import List

logger = get_logger(name="accounts")
router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.post("/", response_model=schemas.TradingAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_trading_account(
    account: schemas.TradingAccountCreate,
    username: str,
    db: Session = Depends(get_db)
):
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
async def get_user_accounts(username: str, db: Session = Depends(get_db)):
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
async def get_trading_account(account_id: int, db: Session = Depends(get_db)):
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
    account_id: int,
    account_update: schemas.TradingAccountUpdate,
    db: Session = Depends(get_db)
):
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