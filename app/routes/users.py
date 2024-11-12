from fastapi import APIRouter, HTTPException, Depends, status, Query, Path, Body
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db
from ..utils.exceptions import DatabaseError
from ..utils.customLogger import get_logger

logger = get_logger(name="users")
router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing credentials"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - Requested resource does not exist"},
        422: {"description": "Validation Error - Invalid input data"},
        500: {"description": "Internal Server Error"}
    }
)

@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    ## Create a New User
    
    Registers a new user with a unique username and optional email address.

    ### Parameters
    - `user` (UserCreate): The user details to create.
    
    ### Returns
    - **201 Created:** The created user object with timestamp and status.
    
    ### Raises
    - **400 Bad Request:** If the username already exists.
    - **422 Unprocessable Entity:** If the input data is invalid.
    - **500 Internal Server Error:** If there's a database error.
    """
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
async def get_users(
    skip: int = Query(0, description="Number of records to skip (pagination)"),
    limit: int = Query(100, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    ## Retrieve a List of Users
    
    Fetches a paginated list of users along with their associated trading accounts.

    ### Parameters
    - `skip` (int, optional): Number of records to skip for pagination. Defaults to 0.
    - `limit` (int, optional): Maximum number of records to return. Defaults to 100.
    
    ### Returns
    - **200 OK:** A list of user objects with their trading accounts.
    
    ### Raises
    - **500 Internal Server Error:** If there's an error fetching the users.
    """
    try:
        users = crud.get_users(db, skip=skip, limit=limit)
        return {"status": "success", "users": users}
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{username}", response_model=schemas.UserResponse)
async def get_user(username: str = Path(..., description="Username of the user"), db: Session = Depends(get_db)):
    """
    ## Get User Details
    
    Retrieves details of a specific user by their username.

    ### Parameters
    - `username` (str): The username of the user to retrieve.
    
    ### Returns
    - **200 OK:** The user object with trading accounts.
    
    ### Raises
    - **404 Not Found:** If the user does not exist.
    - **500 Internal Server Error:** If there's an error fetching the user.
    """
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
async def update_user(
    username: str = Path(..., description="Username of the user to update"),
    user_update: schemas.UserUpdate = Body(..., description="Updated user information"),
    db: Session = Depends(get_db)
):
    """
    ## Update User Information
    
    Updates the details of an existing user.

    ### Parameters
    - `username` (str): The username of the user to update.
    - `user_update` (UserUpdate): The user information to update.
    
    ### Returns
    - **200 OK:** The updated user object.
    
    ### Raises
    - **404 Not Found:** If the user does not exist.
    - **500 Internal Server Error:** If there's an error updating the user.
    """
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