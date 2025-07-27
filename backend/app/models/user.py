from sqlalchemy import (
    Column, String, Boolean, ForeignKey,
    DECIMAL, Integer, DateTime, JSON
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True)
    phone = Column(String(20), unique=True)
    password_hash = Column(String(255))
    avatar_url = Column(String(500))
    bio = Column(String(1000))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    open_id = Column(String(255), unique=True)
    height = Column(DECIMAL(5, 2))
    weight = Column(DECIMAL(5, 2))
    user_type = Column(Integer)
    is_paid = Column(Boolean, default=False)
    region = Column(String(10), nullable=False)
    language = Column(String(10), default='zh-CN')
    timezone = Column(String(50), default='Asia/Shanghai')
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    dietary_restrictions = Column(JSON, default=lambda: [])
    allergies = Column(JSON, default=lambda: [])
    cooking_level = Column(String(20), default='beginner')
    preferred_cuisines = Column(JSON, default=lambda: [])
    exercise_level = Column(Integer, default=1)
    eating_habit = Column(Integer, default=0)
    staple_food_preference = Column(Integer, default=0)
    flavour_preference = Column(JSON, default=lambda: [])
    cooking_type_preference = Column(JSON, default=lambda: [])
    preferred_season = Column(Integer)
    gene_params = Column(JSON)
    notification_settings = Column(JSON, default=lambda: {})
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    user = relationship("User", back_populates="preferences") 