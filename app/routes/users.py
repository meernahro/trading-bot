from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import SessionLocal
from ..utils.customLogger import get_logger

logging = get_logger(name="users")
router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/users", tags=["users"], response_model=schemas.UserResponse)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if user exists
        existing_user = crud.get_user(db, user.username)
        if existing_user:
            raise HTTPException(status_code=400, detail=f"Username {user.username} already exists")
        
        # Create new user
        user_data = user.dict()
        new_user = crud.create_user(db, user_data)
        
        # Return user without sensitive data
        return schemas.UserResponse(
            id=new_user.id,
            username=new_user.username,
            exchange=new_user.exchange,
            market_type=new_user.market_type,
            timestamp=new_user.timestamp
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@router.get("/users", tags=["users"])
async def get_all_users(db: Session = Depends(get_db)):
    try:
        users = crud.get_users(db)
        return {"status": "success", "users": users}
    except Exception as e:
        logging.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 