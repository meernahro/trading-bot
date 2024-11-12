# app/routes/trades.py

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db
from ..utils.exceptions import DatabaseError
from ..utils.customLogger import get_logger
from typing import Optional
from datetime import datetime, timedelta

logger = get_logger(name="trades")
router = APIRouter(prefix="/trades", tags=["trades"])

@router.get("/account/{account_id}", response_model=schemas.TradeListResponse)
async def get_account_trades(
    account_id: int,
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get trades for a specific trading account with optional date filtering
    """
    try:
        # Verify account exists
        account = crud.get_trading_account(db, account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trading account {account_id} not found"
            )

        trades = crud.get_account_trades(db, account_id, skip=skip, limit=limit)
        
        # Filter by date if provided
        if start_date or end_date:
            filtered_trades = []
            for trade in trades:
                if start_date and trade.timestamp < start_date:
                    continue
                if end_date and trade.timestamp > end_date:
                    continue
                filtered_trades.append(trade)
            trades = filtered_trades

        return {"status": "success", "trades": trades}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trades for account {account_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/user/{username}", response_model=schemas.TradeListResponse)
async def get_user_trades(
    username: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get trades for all accounts belonging to a user
    """
    try:
        # Verify user exists
        user = crud.get_user(db, username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {username} not found"
            )

        # Get all user's trading accounts
        accounts = crud.get_user_trading_accounts(db, user.id)
        
        # Collect trades from all accounts
        all_trades = []
        for account in accounts:
            trades = crud.get_account_trades(db, account.id, skip=skip, limit=limit)
            all_trades.extend(trades)
        
        # Sort trades by timestamp (newest first)
        all_trades.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply skip and limit to the combined results
        all_trades = all_trades[skip:skip + limit]

        return {"status": "success", "trades": all_trades}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trades for user {username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/stats/account/{account_id}", response_model=schemas.TradeStatsResponse)
async def get_account_trade_stats(
    account_id: int,
    period: Optional[str] = "all",  # "day", "week", "month", "year", "all"
    db: Session = Depends(get_db)
):
    """
    Get trading statistics for a specific account
    """
    try:
        # Verify account exists
        account = crud.get_trading_account(db, account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trading account {account_id} not found"
            )

        # Calculate date range
        end_date = datetime.utcnow()
        if period == "day":
            start_date = end_date - timedelta(days=1)
        elif period == "week":
            start_date = end_date - timedelta(weeks=1)
        elif period == "month":
            start_date = end_date - timedelta(days=30)
        elif period == "year":
            start_date = end_date - timedelta(days=365)
        else:  # "all"
            start_date = None

        # Get trades within the period
        trades = crud.get_account_trades(db, account_id)
        filtered_trades = [
            trade for trade in trades
            if not start_date or trade.timestamp >= start_date
        ]

        # Calculate statistics
        total_trades = len(filtered_trades)
        total_volume = sum(trade.quantity * trade.price for trade in filtered_trades)
        
        # Calculate win rate and other metrics
        winning_trades = len([
            trade for trade in filtered_trades
            if (trade.side == "BUY" and trade.price < trade.close_price) or
               (trade.side == "SELL" and trade.price > trade.close_price)
        ])
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        return {
            "status": "success",
            "stats": {
                "period": period,
                "total_trades": total_trades,
                "total_volume": total_volume,
                "win_rate": win_rate,
                "start_date": start_date,
                "end_date": end_date
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trade stats for account {account_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

