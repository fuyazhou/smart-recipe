from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.auth import UserSession
from app.utils.auth import verify_token, hash_token
from app.config.settings import settings

# HTTP Bearer认证方案
security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前登录用户"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证令牌
    payload = verify_token(credentials.credentials, "access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌格式错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 查找用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账户已被禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户（已验证）"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账户未验证，请先验证邮箱或手机号"
        )
    return current_user

async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """获取当前用户（可选，不强制要求登录）"""
    if not credentials:
        return None
    
    try:
        payload = verify_token(credentials.credentials, "access")
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            return None
        
        return user
    except:
        return None

def require_region(required_region: str):
    """要求特定地区的用户"""
    def region_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.region != required_region:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"此功能仅限{required_region}地区用户使用"
            )
        return current_user
    return region_checker

def require_verification():
    """要求用户已验证"""
    def verification_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="请先验证您的账户"
            )
        return current_user
    return verification_checker

def require_paid_user():
    """要求付费用户"""
    def paid_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.is_paid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="此功能仅限付费用户使用"
            )
        return current_user
    return paid_checker

async def verify_refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """验证刷新令牌"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供刷新令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = verify_token(credentials.credentials, "refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新令牌无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌格式错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查会话是否有效
    token_hash = hash_token(credentials.credentials)
    session = db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.token_hash == token_hash,
        UserSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="会话已失效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload

class RoleChecker:
    """角色检查器（为将来的角色系统预留）"""
    
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User = Depends(get_current_active_user)):
        # 这里可以添加角色检查逻辑
        # 目前项目中没有角色系统，先预留接口
        return current_user

# 常用的权限检查器
require_admin = RoleChecker(["admin"])
require_moderator = RoleChecker(["admin", "moderator"]) 