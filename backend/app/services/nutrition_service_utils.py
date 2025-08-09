"""
营养计算服务模块
包含各种营养相关的计算功能
"""
from typing import Optional



activity_level_descriptions={
  "activity_levels": {
    "light": {
      "zh": "静态生活方式（办公室职员等工作），长时间久坐偶尔瑜伽或慢走",
      "en": "Sedentary lifestyle (e.g., office worker), prolonged sitting, occasional yoga or slow walking"
    },
    "moderate": {
      "zh": "工作需要站立或走动（销售或交易员等工作），会慢跑、做家务、快走或跳舞等运动",
      "en": "Job requires standing or walking (e.g., salesperson or trader), activities include jogging, housework, brisk walking, or dancing"
    },
    "high": {
      "zh": "重体力职业或休闲方式，会参与竞技体育、快跑或快速自行车等（运动频率为4-5次/周，30 – 60分钟/次）",
      "en": "Physically demanding job or active leisure, involved in competitive sports, fast running, or cycling (exercise 4–5 times/week, 30–60 min/session)"
    }
  }
}





def calculate_energy_intake_vip(
    height_m: float,
    bmi: float,
    activity_level: str,
    stage: str,
    milk_volume_ml: Optional[int] = None
) -> float:
    """
    根据给定的生理参数计算女性在不同阶段的每日推荐能量摄入量 (kcal/d)。

    Args:
        height_m (float): 身高（单位：米）。
        bmi (float): 孕前身体质量指数 (BMI)。
        activity_level (str): 身体活动水平。接受 'light', 'moderate', 'high'。
        stage (str): 生理阶段。接受以下值:
            'pre_conception' (备孕期)
            'early_pregnancy' (孕早期)
            'mid_pregnancy' (孕中期)
            'late_pregnancy' (孕晚期)
            'postpartum_non_lactating' (产后不哺乳)
            'lactating_0_6_months' (哺乳期6个月以内)
            'lactating_6_plus_months' (哺乳期6个月以后 & 混合喂养)
        milk_volume_ml (int, optional): 每日泌乳量（单位：毫升）。
            仅在 stage 为 'lactating_6_plus_months' 时需要。Defaults to None.

    Returns:
        float: 计算得出的每日推荐能量摄入量 (kcal/d)。

    Raises:
        ValueError: 如果输入了无效的参数。
    """
    # 1. 根据BMI确定能量系数
    if bmi <= 18.5:
        energy_coefficient = 37.5
    elif 18.5 < bmi < 24:
        energy_coefficient = 32.5
    elif bmi >= 24.0:
        # BMI 24-27.9 和 BMI >= 28 的能量系数相同
        energy_coefficient = 27.5
    else:
        raise ValueError("无效的 BMI 值。")

    # 2. 计算轻体力活动的基础能量需求
    # 公式: 21.2 * 身高(m)^2 * 能量系数
    base_energy_light = 21.2 * (height_m ** 2) * energy_coefficient

    # 3. 根据实际活动水平进行调整
    pal_map = {
        'light': 1.50,
        'moderate': 1.75,
        'high': 2.00
    }
    if activity_level not in pal_map:
        raise ValueError("activity_level 参数必须是 'light', 'moderate', 或 'high' 之一。")
    
    pal_factor = pal_map[activity_level]
    # 从轻体力活动能量换算到指定活动水平的能量
    # 公式: (轻体力活动能量 / 1.5) * 目标活动水平系数
    activity_adjusted_base_energy = (base_energy_light / 1.5) * pal_factor

    # 4. 根据不同生理阶段计算最终能量
    final_energy = 0.0
    
    # 适用于不增加能量的阶段
    if stage in ['pre_conception', 'early_pregnancy', 'postpartum_non_lactating']:
        final_energy = activity_adjusted_base_energy
    
    # 孕中期
    elif stage == 'mid_pregnancy':
        final_energy = activity_adjusted_base_energy + 300
    
    # 孕晚期
    elif stage == 'late_pregnancy':
        final_energy = activity_adjusted_base_energy + 450
        
    # 哺乳期 0-6 个月
    elif stage == 'lactating_0_6_months':
        # 对超重(BMI 24-27.9)的女性有特殊规则
        if 24.0 <= bmi <= 27.9:
            final_energy = activity_adjusted_base_energy + 300
        else:
            final_energy = activity_adjusted_base_energy + 500
    
    # 哺乳期 6 个月以上或混合喂养
    elif stage == 'lactating_6_plus_months':
        if milk_volume_ml is None or milk_volume_ml < 0:
            raise ValueError("当 stage 为 'lactating_6_plus_months' 时，必须提供 milk_volume_ml。")
        # 公式: 基础能量 + (泌乳量(ml) * 0.85) - 170
        final_energy = activity_adjusted_base_energy + (milk_volume_ml * 0.85) - 170
    
    else:
        valid_stages = [
            'pre_conception', 'early_pregnancy', 'mid_pregnancy', 'late_pregnancy',
            'postpartum_non_lactating', 'lactating_0_6_months', 'lactating_6_plus_months'
        ]
        raise ValueError(f"无效的 stage 参数。请从以下选项中选择: {valid_stages}")

    return final_energy



def calculate_adjusted_energy_vip(stage, pre_pregnancy_bmi, weight_change_rate, current_energy):
    """
    根据孕期/哺乳期阶段、孕前BMI、体重变化和当前能量摄入，计算调整后的能量值。

    参数:
    stage (str): 当前所处阶段。
                 可选值为: 'early_pregnancy', 'mid_pregnancy', 'late_pregnancy',
                            'lactating_0_6_months', 'lactating_6_plus_months'
    pre_pregnancy_bmi (float): 孕前身体质量指数 (BMI)。
    weight_change_rate (float): 体重变化率。
                                - 'early_pregnancy': 整个孕早期的总增重 (kg)。
                                - 'mid_pregnancy', 'late_pregnancy': 每周的增重 (kg/周)。
                                - 'postpartum_...': 每月的体重变化 (kg/月), 负数代表下降。
    current_energy (float or int): 当前每日的能量摄入值 (例如: 2000 kcal)。

    返回:
    tuple: 一个包含两个元素的元组:
           - adjusted_energy (float): 调整后的新每日能量摄入建议值。
           - description (str): 描述本次调整的说明文字。

    假设您当前每日摄入2200千卡（kcal）。

    **示例 1：孕中晚期，体重增长过快**
    * **情况**: 孕前BMI为22，孕中晚期每周增重0.625kg，当前能量摄入2200 kcal。
    * **调用**:

    ```python
    # 示例 1
    new_energy, reason = calculate_adjusted_energy(
        stage='mid_pregnancy',
        pre_pregnancy_bmi=22,
        weight_change_rate=0.625,
        current_energy=2200
    )

    print(f"调整后能量: {new_energy} kcal")
    print(f"调整原因: {reason}")
    # 预期输出:
    # 调整后能量: 1980 kcal
    # 调整原因: 体重增长过速，能量减少10% (Excessive weight gain, Energy -10%)

    
    """
    
    adjustment_factor = 1.0  # 默认为1.0，即不调整
    description = "体重在正常范围，无需调整能量 (Weight is within the normal range, no adjustment needed.)"

    # 1. 根据输入条件判断调整系数 (adjustment_factor)
    # 妊娠早期 (Early Pregnancy)
    if stage == 'early_pregnancy':
        if weight_change_rate > 2:
            adjustment_factor = 0.9
            description = "体重增长过速，能量减少10% (Excessive weight gain, Energy -10%)"
        elif weight_change_rate < 0:
            adjustment_factor = 1.1
            description = "体重下降，能量增加10% (Weight loss, Energy +10%)"

    # 妊娠中晚期 (Mid-to-Late Pregnancy)
    elif stage in ['mid_pregnancy', 'late_pregnancy']:
        if pre_pregnancy_bmi <= 18.5:
            if weight_change_rate > 0.56:
                adjustment_factor = 0.9
                description = "体重增长过速，能量减少10% (Excessive weight gain, Energy -10%)"
            elif weight_change_rate < 0.37:
                adjustment_factor = 1.1
                description = "体重增长过缓，能量增加10% (Insufficient weight gain, Energy +10%)"
        elif 18.5 < pre_pregnancy_bmi <= 23.9:
            if weight_change_rate > 0.48:
                adjustment_factor = 0.9
                description = "体重增长过速，能量减少10% (Excessive weight gain, Energy -10%)"
            elif weight_change_rate < 0.26:
                adjustment_factor = 1.1
                description = "体重增长过缓，能量增加10% (Insufficient weight gain, Energy +10%)"
        elif 24 <= pre_pregnancy_bmi <= 27.9:
            if weight_change_rate > 0.37:
                adjustment_factor = 0.9
                description = "体重增长过速，能量减少10% (Excessive weight gain, Energy -10%)"
            elif weight_change_rate < 0.22:
                adjustment_factor = 1.1
                description = "体重增长过缓，能量增加10% (Insufficient weight gain, Energy +10%)"
        elif pre_pregnancy_bmi >= 28:
            if weight_change_rate > 0.3:
                adjustment_factor = 0.9
                description = "体重增长过速，能量减少10% (Excessive weight gain, Energy -10%)"
            elif weight_change_rate < 0.15:
                adjustment_factor = 1.1
                description = "体重增长过缓，能量增加10% (Insufficient weight gain, Energy +10%)"

    # 哺乳期6个月内 (Postpartum within 6 months)
    elif stage == 'lactating_0_6_months':
        if weight_change_rate > -0.8:  # 每月减重不足0.8kg或体重增加
            adjustment_factor = 0.9
            description = "体重下降未达标，能量减少10% (Weight loss target not met, Energy -10%)"
        else:
            description = "体重下降已达标，无需调整能量 (Weight loss is on track, no adjustment needed.)"
    
    # 哺乳期6个月后及混合喂养 (Postpartum after 6 months or mixed feeding)
    elif stage == 'lactating_6_plus_months':
        if weight_change_rate > 0:
            adjustment_factor = 0.9
            description = "体重增加，能量减少10% (Weight gain, Energy -10%)"
        else:
            description = "体重保持稳定或下降，无需调整能量 (Weight is stable or decreasing, no adjustment needed.)"
            
    else:
        return (current_energy, "输入的阶段无效，请检查。 (Invalid stage input, please check.)")

    # 2. 计算调整后的能量值
    adjusted_energy = round(current_energy * adjustment_factor)
    
    return (adjusted_energy, description)



def calculate_macronutrients_vip(energy_kcal: float, bmi: float) -> dict:
    """
    根据总能量和 BMI 计算三大营养素（脂肪、蛋白质、碳水化合物）的每日摄入推荐量（克）

    参数：
    - energy_kcal: 总能量（单位：千卡）
    - bmi: 身体质量指数（BMI）

    返回：
    - 包含脂肪、蛋白质、碳水化合物摄入量（单位：克）的字典
    """
    # 脂肪：固定 25%
    fat_g = energy_kcal * 0.25 / 9

    # 蛋白质比例
    if bmi < 24:
        protein_ratio = 0.15
    else:
        protein_ratio = 0.20
    protein_g = energy_kcal * protein_ratio / 4

    # 碳水化合物比例
    if bmi < 24:
        carb_ratio = 0.60
    else:
        carb_ratio = 0.55
    carbs_g = energy_kcal * carb_ratio / 4

    return {
        'Fat (g)': round(fat_g, 2),
        'Protein (g)': round(protein_g, 2),
        'Carbohydrates (g)': round(carbs_g, 2)
    }





def male_nutrient_targets_free(age_group: str = "18-49", activity_level: str = "moderate") -> dict:
    """
    返回指定年龄段和身体活动水平的男性每日营养素摄入推荐值。

    参数：
    - age_group: 年龄段（目前仅支持 "18-49"）
    - activity_level: 身体活动水平，可选项：'light', 'moderate', 'high'

    返回：
    - dict，包括能量 (kcal)、脂肪 (g)、蛋白质 (g)、碳水 (g)
    """
    if age_group != "18-49":
        raise ValueError("当前函数仅支持年龄段 '18-49'")

    eer_values = {
        'light': 2250,
        'moderate': 2600,
        'high': 3000
    }

    if activity_level not in eer_values:
        raise ValueError("activity_level 仅支持 'light', 'moderate', 'high'")

    energy = eer_values[activity_level]

    fat_g = round(energy * 0.25 / 9, 2)
    protein_g = round(energy * 0.15 / 4, 2)
    carbs_g = round(energy * 0.60 / 4, 2)

    return {
        'Energy (kcal)': energy,
        'Fat (g)': fat_g,
        'Protein (g)': protein_g,
        'Carbohydrates (g)': carbs_g
    }