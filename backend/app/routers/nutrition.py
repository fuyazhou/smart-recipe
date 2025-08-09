"""
营养相关的API路由
"""
from fastapi import APIRouter, HTTPException, status
from app.schemas.nutrition import EnergyIntakeRequest, EnergyIntakeResponse
from app.services.nutrition_service_utils import calculate_energy_intake_vip as calculate_energy_intake

router = APIRouter()


@router.post("/energy-intake", response_model=EnergyIntakeResponse)
async def calculate_daily_energy_intake(request: EnergyIntakeRequest):
    """
    计算女性在不同生理阶段的每日推荐能量摄入量
    
    根据身高、BMI、活动水平和生理阶段等参数，计算出个性化的每日能量摄入建议。
    支持备孕期、孕期各阶段、产后及哺乳期的能量需求计算。
    """
    try:
        daily_energy = calculate_energy_intake(
            height_m=request.height_m,
            bmi=request.bmi,
            activity_level=request.activity_level,
            stage=request.stage,
            milk_volume_ml=request.milk_volume_ml
        )
        
        return EnergyIntakeResponse(
            daily_energy_kcal=round(daily_energy, 1),
            height_m=request.height_m,
            bmi=request.bmi,
            activity_level=request.activity_level,
            stage=request.stage,
            milk_volume_ml=request.milk_volume_ml
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="计算能量摄入时发生错误"
        )
