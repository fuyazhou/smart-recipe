from sqlalchemy.orm import Session
from datetime import date
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
        gender=user.gender,
        date_of_birth=user.date_of_birth,
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


def compute_bmi(height_m: float | None, weight_kg: float | None) -> float | None:
    if not height_m or not weight_kg or height_m <= 0:
        return None
    return round(float(weight_kg) / (float(height_m) ** 2), 2)


def compute_age(dob: date | None) -> int | None:
    if not dob:
        return None
    today = date.today()
    years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return years


def build_user_health_profile(user: User) -> dict:
    """Aggregate user's health-related profile for clients.
    Includes personal info, health status, activity level, allergies, dietary restrictions, goals, and computed BMI/age.
    """
    preferences = user.preferences
    return {
        "id": user.id,
        "username": user.username,
        "gender": user.gender,
        "date_of_birth": user.date_of_birth.isoformat() if user.date_of_birth else None,
        "age": compute_age(user.date_of_birth),
        "height_m": float(user.height) if user.height is not None else None,
        "weight_kg": float(user.weight) if user.weight is not None else None,
        "bmi": compute_bmi(float(user.height) if user.height else None, float(user.weight) if user.weight else None),
        "activity_level": preferences.activity_level if preferences else None,
        "life_stage": preferences.life_stage if preferences else None,
        "allergies": preferences.allergies if preferences else [],
        "dietary_restrictions": preferences.dietary_restrictions if preferences else [],
        "goals": preferences.goals if preferences else [],
        "medical_conditions": preferences.medical_conditions if preferences else [],
    }

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not pwd_context.verify(password, user.password_hash):
        return None
    return user 