from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, date

class GeneParams(BaseModel):
    nutrient_list: List[int] = []
    requirement_list: List[int] = []

# Base models
class UserPreferenceBase(BaseModel):
    dietary_restrictions: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    cooking_level: Optional[str] = 'beginner'
    preferred_cuisines: Optional[List[str]] = []
    # Unified activity level
    activity_level: Optional[Literal['light', 'moderate', 'high']] = None
    # Deprecated: kept for backward compatibility with old clients
    exercise_level: Optional[int] = Field(1, ge=0, le=3)
    eating_habit: Optional[int] = Field(0, ge=0, le=7)
    staple_food_preference: Optional[int] = Field(0, ge=0, le=2)
    flavour_preference: Optional[List[str]] = []
    cooking_type_preference: Optional[List[str]] = []
    preferred_season: Optional[int] = Field(None, ge=1, le=4)
    gene_params: Optional[GeneParams] = None
    notification_settings: Optional[Dict[str, Any]] = {}
    # Health status & goals
    life_stage: Optional[Literal[
        'pre_conception', 'early_pregnancy', 'mid_pregnancy', 'late_pregnancy',
        'postpartum_non_lactating', 'lactating_0_6_months', 'lactating_6_plus_months',
        'adult_male', 'adult_female'
    ]] = None
    goals: Optional[List[Literal['weight_management', 'nutrition_optimization', 'condition_management']]] = []
    medical_conditions: Optional[List[str]] = []

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    height: Optional[float] = Field(None, gt=0)
    weight: Optional[float] = Field(None, gt=0)
    gender: Optional[Literal['male', 'female', 'other', 'unspecified']] = None
    date_of_birth: Optional[date] = None
    user_type: Optional[int] = None
    is_paid: Optional[bool] = False
    region: str

# For creating new data
class UserPreferenceCreate(UserPreferenceBase):
    pass

class UserCreate(UserBase):
    password: str
    preferences: Optional[UserPreferenceCreate] = None
    open_id: Optional[str] = None

# For updating data
class UserPreferenceUpdate(UserPreferenceBase):
    pass

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    height: Optional[float] = Field(None, gt=0)
    weight: Optional[float] = Field(None, gt=0)
    gender: Optional[Literal['male', 'female', 'other', 'unspecified']] = None
    date_of_birth: Optional[date] = None
    user_type: Optional[int] = None
    is_paid: Optional[bool] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    preferences: Optional[UserPreferenceUpdate] = None

# For reading data (API responses)
class UserPreferenceInDB(UserPreferenceBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserInDB(UserBase):
    id: str
    open_id: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    preferences: Optional[UserPreferenceInDB] = None

    class Config:
        from_attributes = True

class UserPublicProfile(BaseModel):
    id: str
    username: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True 