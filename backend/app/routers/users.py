from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User, UserPreference
from app.schemas.user import UserCreate, UserUpdate, UserInDB, UserPublicProfile
from app.services import user_service

router = APIRouter()

@router.post("/", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.
    """
    if user.email:
        db_user = user_service.get_user_by_email(db, email=user.email)
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = user_service.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    if user.open_id:
        db_user = user_service.get_user_by_open_id(db, open_id=user.open_id)
        if db_user:
            raise HTTPException(status_code=400, detail="Open ID already registered")

    return user_service.create_user(db=db, user=user)

@router.get("/{user_id}", response_model=UserPublicProfile)
def read_user(user_id: str, db: Session = Depends(get_db)):
    """
    Get a user's public profile by ID or username.
    """
    # 首先尝试按ID查找
    db_user = user_service.get_user(db, user_id=user_id)
    
    # 如果找不到，尝试按用户名查找
    if not db_user:
        db_user = user_service.get_user_by_username(db, username=user_id)
        
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/", response_model=List[UserPublicProfile])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of users.
    """
    users = user_service.get_users(db, skip=skip, limit=limit)
    return users 