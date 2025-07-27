import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.user import User
from app.models.auth import UserSession

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==================== 密码相关 ====================

def hash_password(password: str) -> str:
    """加密密码"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def generate_password_hash(password: str) -> str:
    """生成密码哈希 (兼容旧版本)"""
    return hash_password(password)

# ==================== JWT Token 相关 ====================

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=30)  # 刷新令牌有效期30天
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        # 检查令牌类型
        if payload.get("type") != token_type:
            return None
            
        # 检查过期时间
        exp = payload.get("exp")
        if exp is None or datetime.utcfromtimestamp(exp) < datetime.utcnow():
            return None
            
        return payload
    except JWTError:
        return None

def decode_token(token: str) -> Dict[str, Any]:
    """解码JWT令牌（不验证）"""
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )

# ==================== 验证码相关 ====================

def generate_verification_code(length: int = 6, digits_only: bool = True) -> str:
    """生成验证码"""
    if digits_only:
        return ''.join(secrets.choice('0123456789') for _ in range(length))
    else:
        alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_secure_token(length: int = 32) -> str:
    """生成安全令牌"""
    return secrets.token_urlsafe(length)

def hash_token(token: str) -> str:
    """对令牌进行哈希处理"""
    return hashlib.sha256(token.encode()).hexdigest()

# ==================== 用户认证 ====================

def authenticate_user(db: Session, identifier: str, password: str) -> Optional[User]:
    """用户认证"""
    from app.services.user_service import get_user_by_email, get_user_by_username, get_user_by_phone
    
    user = None
    
    # 尝试不同的登录方式
    if "@" in identifier:
        # 邮箱登录
        user = get_user_by_email(db, identifier)
    elif identifier.startswith("+"):
        # 手机号登录
        user = get_user_by_phone(db, identifier)
    else:
        # 用户名登录
        user = get_user_by_username(db, identifier)
    
    if not user:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    return user

def create_user_tokens(user: User) -> Dict[str, Union[str, int]]:
    """为用户创建访问令牌和刷新令牌"""
    token_data = {
        "sub": user.id,
        "username": user.username,
        "region": user.region
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": user.id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_EXPIRE_MINUTES * 60  # 转换为秒
    }

# ==================== 第三方登录辅助 ====================

def generate_oauth_state() -> str:
    """生成OAuth状态参数"""
    return secrets.token_urlsafe(32)

def validate_oauth_state(state: str, stored_state: str) -> bool:
    """验证OAuth状态参数"""
    return secrets.compare_digest(state, stored_state)

# ==================== 安全检查 ====================

def is_password_strong(password: str) -> tuple[bool, list]:
    """检查密码强度"""
    errors = []
    
    if len(password) < 8:
        errors.append("密码长度至少8位")
    
    if not any(c.islower() for c in password):
        errors.append("密码需包含小写字母")
    
    if not any(c.isupper() for c in password):
        errors.append("密码需包含大写字母")
    
    if not any(c.isdigit() for c in password):
        errors.append("密码需包含数字")
    
    # 可选：特殊字符检查
    special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    if not any(c in special_chars for c in password):
        errors.append("建议包含特殊字符以提高安全性")
    
    return len(errors) == 0, errors

def check_account_locked(db: Session, user_id: str) -> tuple[bool, Optional[datetime]]:
    """检查账户是否被锁定"""
    from app.models.auth import AccountLock
    
    lock = db.query(AccountLock).filter(
        AccountLock.user_id == user_id,
        AccountLock.is_active == True,
        AccountLock.locked_until > datetime.utcnow()
    ).first()
    
    if lock:
        return True, lock.locked_until
    return False, None

def record_login_attempt(db: Session, identifier: str, ip_address: str, 
                        user_agent: str, success: bool, failure_reason: str = None):
    """记录登录尝试"""
    from app.models.auth import LoginAttempt
    
    attempt = LoginAttempt(
        identifier=identifier,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        failure_reason=failure_reason
    )
    db.add(attempt)
    db.commit()

# ==================== 会话管理 ====================

def create_user_session(db: Session, user_id: str, token_hash: str, 
                       device_info: dict, ip_address: str, expires_at: datetime) -> UserSession:
    """创建用户会话"""
    session = UserSession(
        user_id=user_id,
        token_hash=token_hash,
        device_info=device_info,
        ip_address=ip_address,
        expires_at=expires_at
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def invalidate_user_session(db: Session, session_id: str):
    """失效用户会话"""
    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if session:
        session.is_active = False
        db.commit()

def invalidate_all_user_sessions(db: Session, user_id: str):
    """失效用户所有会话"""
    db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.is_active == True
    ).update({"is_active": False})
    db.commit()

# ==================== 邮箱/手机号验证 ====================

def validate_email_format(email: str) -> bool:
    """验证邮箱格式"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone_format(phone: str, region: str) -> bool:
    """验证手机号格式"""
    if region == "china":
        # 中国手机号：+86 + 11位数字
        import re
        pattern = r'^\+86\d{11}$'
        return re.match(pattern, phone) is not None
    else:  # us
        # 美国手机号：+1 + 10位数字
        import re
        pattern = r'^\+1\d{10}$'
        return re.match(pattern, phone) is not None

def normalize_phone_number(phone: str, region: str) -> str:
    """标准化手机号格式"""
    # 移除所有非数字字符
    digits_only = ''.join(filter(str.isdigit, phone))
    
    if region == "china":
        if len(digits_only) == 11:
            return f"+86{digits_only}"
        elif len(digits_only) == 13 and digits_only.startswith("86"):
            return f"+{digits_only}"
    else:  # us
        if len(digits_only) == 10:
            return f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith("1"):
            return f"+{digits_only}"
    
    return phone  # 返回原始格式如果无法标准化 