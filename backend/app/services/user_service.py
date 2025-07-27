from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.models.user import User, UserPreference
from app.schemas.user import UserCreate, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user(db: Session, user_id: str):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_open_id(db: Session, open_id: str):
    return db.query(User).filter(User.open_id == open_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        phone=user.phone,
        password_hash=hashed_password,
        height=user.height,
        weight=user.weight,
        user_type=user.user_type,
        is_paid=user.is_paid,
        region=user.region,
        open_id=user.open_id
    )

    if user.preferences:
        db_preferences = UserPreference(**user.preferences.dict())
        db_user.preferences = db_preferences

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user: User, user_update: UserUpdate):
    update_data = user_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        if key == "preferences":
            if user.preferences:
                for pref_key, pref_value in value.items():
                    setattr(user.preferences, pref_key, pref_value)
            else:
                db_preferences = UserPreference(**value)
                user.preferences = db_preferences
        else:
            setattr(user, key, value)
            
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not pwd_context.verify(password, user.password_hash):
        return None
    return user 