from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db
from ..utils.exceptions import DatabaseError
from ..utils.customLogger import get_logger

logger = get_logger(name="users")
router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        existing_user = crud.get_user(db, user.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username {user.username} already exists"
            )
        
        return crud.create_user(db, user)
    except DatabaseError as e:
        logger.error(f"Database error while creating user: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while creating user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/", response_model=schemas.UserListResponse)
async def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        users = crud.get_users(db, skip=skip, limit=limit)
        return {"status": "success", "users": users}
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{username}", response_model=schemas.UserResponse)
async def get_user(username: str, db: Session = Depends(get_db)):
    try:
        user = crud.get_user(db, username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {username} not found"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user {username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{username}", response_model=schemas.UserResponse)
async def update_user(username: str, user_update: schemas.UserUpdate, db: Session = Depends(get_db)):
    try:
        updated_user = crud.update_user(db, username, user_update)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {username} not found"
            )
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))