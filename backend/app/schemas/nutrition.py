"""
营养相关的Pydantic模式定义
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal


class EnergyIntakeRequest(BaseModel):
    """能量摄入计算请求模式"""
    height_m: float = Field(..., description="身高（单位：米）", gt=0, le=3)
    bmi: float = Field(..., description="孕前身体质量指数 (BMI)", gt=10, le=50)
    activity_level: Literal['light', 'moderate', 'high'] = Field(..., description="身体活动水平")
    stage: Literal[
        'pre_conception', 
        'early_pregnancy', 
        'mid_pregnancy', 
        'late_pregnancy',
        'postpartum_non_lactating', 
        'lactating_0_6_months', 
        'lactating_6_plus_months'
    ] = Field(..., description="生理阶段")
    milk_volume_ml: Optional[int] = Field(None, description="每日泌乳量（单位：毫升）", ge=0)

    @validator('milk_volume_ml')
    def validate_milk_volume(cls, v, values):
        """验证泌乳量参数"""
        stage = values.get('stage')
        if stage == 'lactating_6_plus_months' and v is None:
            raise ValueError("当 stage 为 'lactating_6_plus_months' 时，必须提供 milk_volume_ml")
        if stage != 'lactating_6_plus_months' and v is not None:
            raise ValueError("只有当 stage 为 'lactating_6_plus_months' 时才能提供 milk_volume_ml")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "height_m": 1.65,
                "bmi": 22.0,
                "activity_level": "moderate",
                "stage": "mid_pregnancy",
                "milk_volume_ml": None
            }
        }


class EnergyIntakeResponse(BaseModel):
    """能量摄入计算响应模式"""
    daily_energy_kcal: float = Field(..., description="每日推荐能量摄入量 (kcal/d)")
    height_m: float = Field(..., description="身高（单位：米）")
    bmi: float = Field(..., description="BMI")
    activity_level: str = Field(..., description="身体活动水平")
    stage: str = Field(..., description="生理阶段")
    milk_volume_ml: Optional[int] = Field(None, description="每日泌乳量（单位：毫升）")

    class Config:
        json_schema_extra = {
            "example": {
                "daily_energy_kcal": 2100.5,
                "height_m": 1.65,
                "bmi": 22.0,
                "activity_level": "moderate",
                "stage": "mid_pregnancy",
                "milk_volume_ml": None
            }
        }
