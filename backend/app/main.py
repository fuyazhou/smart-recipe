from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import os

from app.config.settings import settings
from app.database import create_tables
from app.routers import users

# 创建FastAPI应用实例
app = FastAPI(
    title="Smart Recipe API",
    description="多平台智能食谱应用后端API",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# 添加中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(users.router, prefix="/api/v1/users", tags=["用户"])

# 导入认证路由
from app.routers import auth
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])

# 初始化数据库表
@app.on_event("startup")
async def startup_event():
    create_tables()

@app.get("/")
async def root():
    """根路径，返回API状态信息"""
    return {
        "message": "Smart Recipe API",
        "version": "1.0.0",
        "region": settings.REGION,
        "environment": settings.ENVIRONMENT,
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "region": settings.REGION}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 