from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    APP_NAME: str = "smart-recipe"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    REGION: str = "china"  # china 或 us
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/smart_recipe"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT配置
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://*.smartrecipe.com",
    ]
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]
    
    # 第三方服务配置（根据地区不同）
    @property
    def payment_config(self) -> dict:
        if self.REGION == "china":
            return {
                "wechat_pay_app_id": os.getenv("WECHAT_PAY_APP_ID"),
                "wechat_pay_merchant_id": os.getenv("WECHAT_PAY_MERCHANT_ID"),
                "alipay_app_id": os.getenv("ALIPAY_APP_ID"),
            }
        else:  # us
            return {
                "stripe_publishable_key": os.getenv("STRIPE_PUBLISHABLE_KEY"),
                "stripe_secret_key": os.getenv("STRIPE_SECRET_KEY"),
            }
    
    @property
    def map_config(self) -> dict:
        if self.REGION == "china":
            return {
                "provider": "amap",
                "api_key": os.getenv("AMAP_API_KEY"),
            }
        else:  # us
            return {
                "provider": "google",
                "api_key": os.getenv("GOOGLE_MAPS_API_KEY"),
            }
    
    @property
    def sms_config(self) -> dict:
        if self.REGION == "china":
            return {
                "provider": "aliyun",
                "access_key": os.getenv("ALIYUN_SMS_ACCESS_KEY"),
                "secret_key": os.getenv("ALIYUN_SMS_SECRET_KEY"),
            }
        else:  # us
            return {
                "provider": "twilio",
                "account_sid": os.getenv("TWILIO_ACCOUNT_SID"),
                "auth_token": os.getenv("TWILIO_AUTH_TOKEN"),
            }
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings() 